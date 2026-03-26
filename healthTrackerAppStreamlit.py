import asyncio
import csv
import json
import os
import shutil
import tempfile
import sys
import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from Agents.HealthReport_InformationAgent import extract_context_from_pdf

sys.path.append(os.path.join(os.path.dirname(__file__), "medical_extractor_project"))
from medical_extractor_project.main import report_parameters_extractor

load_dotenv()
from Agents.HealthReportParameterAgent import extract_from_pdf

from fitness_metrics import (
    workout_count_per_week,
    volume_load_per_session,
    weekly_hard_sets_per_muscle,
    estimated_1rm_trend,
    prs_this_month,
    daily_macros,
    calorie_adherence,
    protein_adherence,
    workout_adherence,
    food_logging_adherence,
    training_score,
    nutrition_score,
    consistency_score,
    load_sessions,
    load_sets_with_exercises,
)
from recommendations import generate_recommendations

db_config = st.secrets["database_docker"]

os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY", "")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "health_monitoring_streamlit"

DB_CONFIG = {
    "host": db_config["host"],
    "port": db_config["port"],
    "user": db_config["user"],
    "password": db_config["password"],
    "database": db_config["database"],
}

MUSCLE_GROUPS = ["chest", "back", "legs", "shoulders", "arms", "core", "full_body"]
EQUIPMENT_OPTIONS = ["barbell", "dumbbell", "cable", "machine", "bodyweight", "kettlebell", "other"]
GOAL_TYPES = ["muscle_gain", "fat_loss", "recomposition"]

# ──────────────────────────────────────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def _column_exists(cursor, table, column):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (DB_CONFIG["database"], table, column),
    )
    return cursor.fetchone()[0] > 0


def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userId INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_intake (
            user VARCHAR(255),
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_id INT,
            date DATE NOT NULL,
            meal_type VARCHAR(255) NOT NULL,
            food_item VARCHAR(255),
            quantity FLOAT,
            unit VARCHAR(255)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_item VARCHAR(255) NOT NULL,
            serving_size VARCHAR(255) NOT NULL,
            protein FLOAT NOT NULL,
            fat FLOAT NOT NULL,
            calories FLOAT NOT NULL,
            UNIQUE (food_item)
        )
    """)

    if not _column_exists(cursor, "food_items", "carbs"):
        cursor.execute("ALTER TABLE food_items ADD COLUMN carbs FLOAT DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_intake (
            user VARCHAR(255),
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            water_intake FLOAT NOT NULL,
            UNIQUE (date)
        )
    """)

    # ── V1 fitness tables ────────────────────────────────────────────────────

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            muscle_group VARCHAR(100) NOT NULL,
            equipment VARCHAR(100) DEFAULT 'other',
            is_active TINYINT(1) DEFAULT 1,
            UNIQUE (name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_goals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            goal_type VARCHAR(50) NOT NULL DEFAULT 'fat_loss',
            calorie_target FLOAT DEFAULT 0,
            protein_target FLOAT DEFAULT 0,
            carb_target FLOAT DEFAULT 0,
            fat_target FLOAT DEFAULT 0,
            training_days_per_week INT DEFAULT 4,
            UNIQUE (user)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            session_date DATE NOT NULL,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_sets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            exercise_id INT NOT NULL,
            set_order INT NOT NULL,
            reps INT NOT NULL,
            weight FLOAT NOT NULL DEFAULT 0,
            rpe FLOAT,
            rir INT,
            FOREIGN KEY (session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS body_photos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            taken_date DATE NOT NULL,
            file_path VARCHAR(512) NOT NULL,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS body_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            weight_kg FLOAT,
            waist_cm FLOAT,
            UNIQUE (user, date)
        )
    """)

    seed_exercises(cursor, conn)
    update_food_items_from_excel(cursor, conn)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Seed exercises (insert-if-missing only)
# ──────────────────────────────────────────────────────────────────────────────

def seed_exercises(cursor, conn):
    seed_path = os.path.join(os.path.dirname(__file__), "data", "exercises_seed.csv")
    if not os.path.exists(seed_path):
        return
    try:
        with open(seed_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute(
                    "INSERT IGNORE INTO exercises (name, muscle_group, equipment) VALUES (%s, %s, %s)",
                    (row["name"].strip(), row["muscle_group"].strip(), row.get("equipment", "other").strip()),
                )
        conn.commit()
    except Exception as e:
        print(f"Error seeding exercises: {e}")


def update_food_items_from_excel(cursor, conn):
    try:
        df = pd.read_excel("food_items.xlsx")
        df.columns = [col.strip().lower() for col in df.columns]

        required_columns = ["food item", "serving size (100 g)", "protein", "fat", "calories"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: '{col}' in the Excel file.")

        df.rename(columns={
            "food item": "Food Item",
            "serving size (100 g)": "Serving Size",
            "protein": "Protein",
            "fat": "Fat",
            "calories": "Calories",
        }, inplace=True)
        if "carbs" in [c.lower() for c in df.columns]:
            df.rename(columns={"carbs": "Carbs"}, inplace=True)
        else:
            df["Carbs"] = 0.0

        df = df.astype({"Protein": float, "Fat": float, "Calories": float, "Carbs": float})

        cursor.execute("SELECT food_item, serving_size, protein, fat, calories FROM food_items")
        existing_items = {row[0]: (row[1], row[2], row[3], row[4]) for row in cursor.fetchall()}

        for _, row in df.iterrows():
            food_item = row["Food Item"]
            serving_size = row["Serving Size"]
            protein = row["Protein"]
            fat = row["Fat"]
            calories = row["Calories"]
            carbs = row["Carbs"]

            if (food_item not in existing_items or
                    existing_items[food_item] != (serving_size, protein, fat, calories)):
                cursor.execute("""
                    INSERT INTO food_items (food_item, serving_size, protein, fat, calories, carbs)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    serving_size = VALUES(serving_size),
                    protein = VALUES(protein),
                    fat = VALUES(fat),
                    calories = VALUES(calories),
                    carbs = VALUES(carbs)
                """, (food_item, serving_size, protein, fat, calories, carbs))

        conn.commit()
    except Exception as e:
        print(f"Error updating food items from Excel: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# CRUD helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_food_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, food_item, serving_size FROM food_items")
    food_items = cursor.fetchall()
    conn.close()
    return food_items


def insert_food_intake(food_id, date, meal_type, food_item, quantity, unit):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO food_intake (user, food_id, date, meal_type, food_item, quantity, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (st.session_state.username, food_id, date, meal_type, food_item, quantity, unit))
    conn.commit()
    conn.close()


def insert_water_intake(date, water_intake):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO water_intake (user, date, water_intake)
        VALUES (%s, %s, %s)
    """, (st.session_state.username, date, water_intake))
    conn.commit()
    conn.close()


def delete_last_entry(date, meal_type=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if meal_type:
        cursor.execute("""
            DELETE FROM food_intake
            WHERE date = %s AND meal_type = %s
            ORDER BY id DESC LIMIT 1
        """, (date, meal_type))
    else:
        cursor.execute("DELETE FROM water_intake WHERE date = %s", (date,))
    conn.commit()
    conn.close()


def fetch_last_month_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    one_month_ago = datetime.today() - timedelta(days=30)
    cursor.execute("SELECT * FROM food_intake WHERE date >= %s ORDER BY date DESC", (one_month_ago,))
    food_intake = pd.DataFrame(cursor.fetchall())
    cursor.execute("SELECT * FROM water_intake WHERE date >= %s ORDER BY date DESC", (one_month_ago,))
    water_intake = pd.DataFrame(cursor.fetchall())
    conn.close()
    return food_intake, water_intake


def calculate_metrices():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        WITH user_table AS (SELECT * FROM food_intake WHERE user = %s)
        SELECT date, F1.meal_type,
               SUM(quantity*protein) AS total_protein_per_meal,
               SUM(quantity*fat) AS total_fat_per_meal,
               SUM(quantity*calories) AS total_calories_per_meal
        FROM user_table F1 JOIN food_items F2 ON F1.food_id = F2.id
        GROUP BY date, F1.meal_type
    """, (st.session_state.username,))
    agg_perDay_perMeal = pd.DataFrame(cursor.fetchall())

    cursor.execute("""
        WITH user_table AS (SELECT * FROM food_intake WHERE user = %s)
        SELECT date,
               SUM(total_protein_per_meal) AS total_protein_per_day,
               SUM(total_fat_per_meal)     AS total_fat_per_day,
               SUM(total_calories_per_meal) AS total_calories_per_day
        FROM (
            SELECT date, F1.meal_type,
                   SUM(quantity*protein) AS total_protein_per_meal,
                   SUM(quantity*fat) AS total_fat_per_meal,
                   SUM(quantity*calories) AS total_calories_per_meal
            FROM user_table F1 JOIN food_items F2 ON F1.food_id = F2.id
            GROUP BY date, F1.meal_type
        ) table1
        GROUP BY date
    """, (st.session_state.username,))
    agg_perDay = pd.DataFrame(cursor.fetchall())
    conn.close()
    return agg_perDay_perMeal, agg_perDay


def get_active_exercises(muscle_group=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if muscle_group and muscle_group != "All":
        cursor.execute(
            "SELECT id, name, muscle_group, equipment FROM exercises WHERE is_active = 1 AND muscle_group = %s ORDER BY name",
            (muscle_group,),
        )
    else:
        cursor.execute("SELECT id, name, muscle_group, equipment FROM exercises WHERE is_active = 1 ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_exercises():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM exercises ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_goals(user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_goals WHERE user = %s", (user,))
    row = cursor.fetchone()
    conn.close()
    return row


def upsert_user_goals(user, goal_type, cal, prot, carb, fat, training_days):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_goals (user, goal_type, calorie_target, protein_target, carb_target, fat_target, training_days_per_week)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            goal_type = VALUES(goal_type),
            calorie_target = VALUES(calorie_target),
            protein_target = VALUES(protein_target),
            carb_target = VALUES(carb_target),
            fat_target = VALUES(fat_target),
            training_days_per_week = VALUES(training_days_per_week)
    """, (user, goal_type, cal, prot, carb, fat, training_days))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# UI sections
# ──────────────────────────────────────────────────────────────────────────────

class FoodTab:
    def __init__(self, tab_name):
        self.tab_name = tab_name
        st.subheader("Log your food intake")

        self.selected_meal_type = st.selectbox("Select meal type", ["Breakfast", "Morning Snacks", "Lunch", "Evening Snacks", "Dinner"])
        self.date = st.date_input("Date", value=datetime.today())
        self.food_items = get_food_items()
        self.selected_food_item = st.selectbox("Select Food Item", [f[1] for f in self.food_items])

        self.selected_food_info = next((f for f in self.food_items if f[1] == self.selected_food_item), None)
        self.serving_size = self.selected_food_info[2] if self.selected_food_info else "Unknown"
        self.food_id = self.selected_food_info[0] if self.selected_food_info else "Unknown"
        st.write(f"**Serving Size:** {self.serving_size}")

        self.quantity = st.number_input("Quantity", min_value=0.0, step=0.1)

        if st.button("Add Food"):
            self.save_data()
        if st.button("Delete Last Entry"):
            self.delete_last_entry()

    def save_data(self):
        if self.date and self.selected_food_item and self.quantity:
            insert_food_intake(self.food_id, self.date, self.selected_meal_type, self.selected_food_item, self.quantity, self.serving_size)
            st.success(f"Added {self.selected_food_item} to {self.selected_meal_type} on {self.date}.")
        else:
            st.warning("Please fill in all fields.")

    def delete_last_entry(self):
        if self.date:
            delete_last_entry(self.date, self.selected_meal_type)
            st.success(f"Deleted the last {self.selected_meal_type} entry for {self.date}.")
        else:
            st.warning("Please select a date.")


class WaterIntakeTab:
    def __init__(self):
        st.subheader("Log Your Water Intake")
        self.date = st.date_input("Date", value=datetime.today(), key="water_date")
        self.water_intake = st.number_input("Water Intake (L)", min_value=0.0, step=0.1)

        if st.button("Add Water Intake"):
            self.save_data()
        if st.button("Delete Last Water Intake"):
            self.delete_last_entry()

    def save_data(self):
        if self.date and self.water_intake:
            insert_water_intake(self.date, self.water_intake)
            st.success(f"Added {self.water_intake}L water intake for {self.date}.")
        else:
            st.warning("Please fill in all fields.")

    def delete_last_entry(self):
        if self.date:
            delete_last_entry(self.date)
            st.success(f"Deleted the last water intake entry for {self.date}.")
        else:
            st.warning("Please select a date.")


# ── Workout logging ──────────────────────────────────────────────────────────

def render_workout_log():
    st.subheader("Log Workout")

    session_date = st.date_input("Workout date", value=datetime.today(), key="wk_date")
    session_notes = st.text_input("Session notes (optional)", key="wk_notes")

    if "wk_exercises" not in st.session_state:
        st.session_state.wk_exercises = []

    st.markdown("---")
    st.markdown("**Add an exercise**")
    filter_mg = st.selectbox("Filter by muscle group", ["All"] + MUSCLE_GROUPS, key="wk_mg_filter")
    exercises = get_active_exercises(filter_mg)
    if not exercises:
        st.info("No exercises found. Ask an admin to add exercises to the catalog.")
        return

    ex_names = [e["name"] for e in exercises]
    selected_name = st.selectbox("Exercise", ex_names, key="wk_ex_select")
    selected_ex = next(e for e in exercises if e["name"] == selected_name)

    num_sets = st.number_input("Number of sets", min_value=1, max_value=20, value=3, step=1, key="wk_num_sets")

    with st.expander("What are RPE & RIR?"):
        st.markdown(
            """
**RPE (Rate of Perceived Exertion)** — How hard the set felt on a 1–10 scale (1 very easy, 10 max effort). Leave at **0** if you are not logging RPE for that set.

**RIR (Reps in Reserve)** — How many more good-form reps you could have done after the last rep (**0** = none left). Leave at **-1** if you are not logging RIR for that set.

**Hard sets (Workout dashboard)** — A set counts as hard when **RPE ≥ 7** or **RIR ≤ 3**, if you provide at least one of them. Sets with both missing are ignored for the chart.
"""
        )

    sets_data = []
    cols_header = st.columns([1, 2, 2, 2, 2])
    cols_header[0].markdown("**Set**")
    cols_header[1].markdown("**Weight (kg)**")
    cols_header[2].markdown("**Reps**")
    cols_header[3].markdown("**RPE**")
    cols_header[4].markdown("**RIR**")

    for i in range(int(num_sets)):
        cols = st.columns([1, 2, 2, 2, 2])
        cols[0].write(f"{i + 1}")
        w = cols[1].number_input("w", min_value=0.0, step=2.5, key=f"wk_w_{i}", label_visibility="collapsed")
        r = cols[2].number_input("r", min_value=0, step=1, key=f"wk_r_{i}", label_visibility="collapsed")
        rpe = cols[3].number_input(
            "rpe",
            min_value=0.0,
            max_value=10.0,
            step=0.5,
            value=0.0,
            key=f"wk_rpe_{i}",
            label_visibility="collapsed",
            help="1–10 how hard the set felt (0 = not logged). Dashboard counts a “hard” set when RPE ≥ 7 (or RIR ≤ 3 if you log RIR instead).",
        )
        rir = cols[4].number_input(
            "rir",
            min_value=-1,
            max_value=10,
            step=1,
            value=-1,
            key=f"wk_rir_{i}",
            label_visibility="collapsed",
            help="Reps you could still do with good form (–1 = not logged). Dashboard counts a “hard” set when RIR ≤ 3 (or RPE ≥ 7 if you log RPE instead).",
        )
        sets_data.append({"weight": w, "reps": r, "rpe": rpe if rpe > 0 else None, "rir": rir if rir >= 0 else None})

    if st.button("Add exercise to session", key="wk_add_ex"):
        valid_sets = [s for s in sets_data if s["reps"] > 0]
        if not valid_sets:
            st.warning("Enter at least one set with reps > 0.")
        else:
            st.session_state.wk_exercises.append({
                "exercise_id": selected_ex["id"],
                "exercise_name": selected_ex["name"],
                "muscle_group": selected_ex["muscle_group"],
                "sets": valid_sets,
            })
            st.success(f"Added {selected_ex['name']} ({len(valid_sets)} sets)")
            st.rerun()

    if st.session_state.wk_exercises:
        st.markdown("---")
        st.markdown("**Current session**")
        for idx, ex in enumerate(st.session_state.wk_exercises):
            with st.expander(f"{ex['exercise_name']} — {len(ex['sets'])} sets"):
                for j, s in enumerate(ex["sets"]):
                    st.write(f"  Set {j + 1}: {s['weight']} kg x {s['reps']} reps"
                             + (f" @ RPE {s['rpe']}" if s['rpe'] else "")
                             + (f" | RIR {s['rir']}" if s['rir'] is not None else ""))
                if st.button(f"Remove {ex['exercise_name']}", key=f"wk_rm_{idx}"):
                    st.session_state.wk_exercises.pop(idx)
                    st.rerun()

        if st.button("Finish & save workout", type="primary", key="wk_save"):
            _save_workout(session_date, session_notes, st.session_state.wk_exercises)
            st.session_state.wk_exercises = []
            st.success("Workout saved!")
            st.rerun()


def _save_workout(session_date, notes, exercises_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workout_sessions (user, session_date, notes) VALUES (%s, %s, %s)",
        (st.session_state.username, session_date, notes or None),
    )
    session_id = cursor.lastrowid
    set_order = 1
    for ex in exercises_list:
        for s in ex["sets"]:
            cursor.execute("""
                INSERT INTO exercise_sets (session_id, exercise_id, set_order, reps, weight, rpe, rir)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (session_id, ex["exercise_id"], set_order, s["reps"], s["weight"], s["rpe"], s["rir"]))
            set_order += 1
    conn.commit()
    conn.close()


# ── Goals & Settings ─────────────────────────────────────────────────────────

def render_goals():
    st.subheader("Goals & Targets")
    goals = get_user_goals(st.session_state.username)

    goal_type = st.selectbox("Goal type", GOAL_TYPES, index=GOAL_TYPES.index(goals["goal_type"]) if goals and goals["goal_type"] in GOAL_TYPES else 0, key="g_type")
    cal = st.number_input("Daily calorie target (kcal)", min_value=0.0, step=50.0, value=float(goals["calorie_target"]) if goals else 2000.0, key="g_cal")
    prot = st.number_input("Daily protein target (g)", min_value=0.0, step=5.0, value=float(goals["protein_target"]) if goals else 120.0, key="g_prot")
    carb = st.number_input("Daily carb target (g)", min_value=0.0, step=5.0, value=float(goals["carb_target"]) if goals else 0.0, key="g_carb")
    fat = st.number_input("Daily fat target (g)", min_value=0.0, step=5.0, value=float(goals["fat_target"]) if goals else 0.0, key="g_fat")
    tdays = st.number_input("Training days per week", min_value=1, max_value=7, step=1, value=int(goals["training_days_per_week"]) if goals else 4, key="g_td")

    if st.button("Save goals", key="g_save"):
        upsert_user_goals(st.session_state.username, goal_type, cal, prot, carb, fat, tdays)
        st.success("Goals saved!")


# ── Admin: Exercise catalog ──────────────────────────────────────────────────

def render_admin_exercises():
    st.subheader("Exercise Catalog (Admin)")

    exercises = get_all_exercises()
    if exercises:
        search = st.text_input("Search exercises", key="adm_search")
        filtered = [e for e in exercises if search.lower() in e["name"].lower()] if search else exercises
        df = pd.DataFrame(filtered)
        st.dataframe(df[["id", "name", "muscle_group", "equipment", "is_active"]], use_container_width=True)

    st.markdown("---")
    st.markdown("**Add new exercise**")
    new_name = st.text_input("Name", key="adm_new_name")
    new_mg = st.selectbox("Muscle group", MUSCLE_GROUPS, key="adm_new_mg")
    new_eq = st.selectbox("Equipment", EQUIPMENT_OPTIONS, key="adm_new_eq")

    if st.button("Add exercise", key="adm_add"):
        if not new_name.strip():
            st.warning("Name is required.")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO exercises (name, muscle_group, equipment) VALUES (%s, %s, %s)",
                    (new_name.strip(), new_mg, new_eq),
                )
                conn.commit()
                st.success(f"Added '{new_name.strip()}'")
                st.rerun()
            except mysql.connector.IntegrityError:
                st.error("An exercise with that name already exists.")
            finally:
                conn.close()

    st.markdown("---")
    st.markdown("**Edit / deactivate exercise**")
    if exercises:
        ex_names = [e["name"] for e in exercises]
        edit_name = st.selectbox("Select exercise to edit", ex_names, key="adm_edit_sel")
        edit_ex = next(e for e in exercises if e["name"] == edit_name)

        ed_name = st.text_input("Rename", value=edit_ex["name"], key="adm_ed_name")
        ed_mg = st.selectbox("Muscle group", MUSCLE_GROUPS, index=MUSCLE_GROUPS.index(edit_ex["muscle_group"]) if edit_ex["muscle_group"] in MUSCLE_GROUPS else 0, key="adm_ed_mg")
        ed_eq = st.selectbox("Equipment", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(edit_ex["equipment"]) if edit_ex["equipment"] in EQUIPMENT_OPTIONS else len(EQUIPMENT_OPTIONS) - 1, key="adm_ed_eq")
        ed_active = st.checkbox("Active", value=bool(edit_ex["is_active"]), key="adm_ed_active")

        if st.button("Save changes", key="adm_ed_save"):
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE exercises SET name=%s, muscle_group=%s, equipment=%s, is_active=%s WHERE id=%s
                """, (ed_name.strip(), ed_mg, ed_eq, 1 if ed_active else 0, edit_ex["id"]))
                conn.commit()
                st.success("Updated!")
                st.rerun()
            except mysql.connector.IntegrityError:
                st.error("An exercise with that name already exists.")
            finally:
                conn.close()

        if st.button("Delete exercise", type="secondary", key="adm_del"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM exercise_sets WHERE exercise_id = %s", (edit_ex["id"],))
            ref_count = cursor.fetchone()[0]
            if ref_count > 0:
                st.error(f"Cannot delete — {ref_count} logged set(s) reference this exercise. Deactivate it instead.")
            else:
                cursor.execute("DELETE FROM exercises WHERE id = %s", (edit_ex["id"],))
                conn.commit()
                st.success("Deleted!")
                st.rerun()
            conn.close()


# ── Workout Dashboard ────────────────────────────────────────────────────────

def render_workout_dashboard():
    st.subheader("Workout Dashboard")
    conn = get_db_connection()
    sessions = load_sessions(conn, st.session_state.username, days=60)
    sets_df = load_sets_with_exercises(conn, st.session_state.username, days=60)
    conn.close()

    if sessions.empty:
        st.info("No workouts logged yet. Start by logging a workout!")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Weekly workout count (last 8 weeks)**")
        wc = workout_count_per_week(sessions, weeks=8)
        if not wc.empty:
            fig = px.bar(wc, x="week", y="workouts", text_auto=True)
            fig.update_layout(yaxis_title="Workouts", xaxis_title="Week", height=300)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Volume trend (per session)**")
        vl = volume_load_per_session(sets_df)
        if not vl.empty:
            fig = px.line(vl, x="session_date", y="volume", markers=True)
            fig.update_layout(yaxis_title="Volume (kg x reps)", xaxis_title="Date", height=300)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Top lift progress (estimated 1RM)**")
        if not sets_df.empty:
            exercise_names = sorted(sets_df["exercise_name"].unique())
            pick = st.selectbox("Exercise", exercise_names, key="wd_1rm_ex")
            ex_id = sets_df[sets_df["exercise_name"] == pick]["exercise_id"].iloc[0]
            e1rm = estimated_1rm_trend(sets_df, exercise_id=ex_id)
            if not e1rm.empty:
                fig = px.line(e1rm, x="session_date", y="e1rm", markers=True, title=f"{pick} — est. 1RM")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("**Hard sets by muscle group (last 4 weeks)**")
        hs = weekly_hard_sets_per_muscle(sets_df, weeks=4)
        if not hs.empty:
            fig = px.bar(hs, x="week", y="hard_sets", color="muscle_group", barmode="stack")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Log RPE or RIR on your sets to see hard-set data.")


# ── Nutrition Dashboard ──────────────────────────────────────────────────────

def render_nutrition_dashboard():
    st.subheader("Nutrition Dashboard")
    goals = get_user_goals(st.session_state.username)
    conn = get_db_connection()
    dm = daily_macros(conn, st.session_state.username, days=30)
    food_adh = food_logging_adherence(conn, st.session_state.username, window=7)
    conn.close()

    cal_target = float(goals["calorie_target"]) if goals and goals["calorie_target"] else 0
    prot_target = float(goals["protein_target"]) if goals and goals["protein_target"] else 0

    if dm.empty:
        st.info("No food logged recently. Start logging meals!")
        return

    today_row = dm[dm["date"] == datetime.today().date()]
    col1, col2, col3 = st.columns(3)
    today_cal = float(today_row["calories"].iloc[0]) if not today_row.empty else 0
    today_prot = float(today_row["protein"].iloc[0]) if not today_row.empty else 0

    col1.metric("Calories today", f"{today_cal:.0f} kcal", delta=f"{today_cal - cal_target:.0f} vs target" if cal_target else None)
    col2.metric("Protein today", f"{today_prot:.0f} g", delta=f"{today_prot - prot_target:.0f} vs target" if prot_target else None)
    col3.metric("Meal log consistency (7d)", f"{food_adh * 100:.0f}%")

    st.markdown("---")

    col4, col5 = st.columns(2)
    with col4:
        st.markdown("**Weekly macro averages**")
        dm["date"] = pd.to_datetime(dm["date"])
        dm["week"] = dm["date"].apply(lambda d: f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}")
        weekly = dm.groupby("week")[["calories", "protein", "fat", "carbs"]].mean().reset_index()
        if not weekly.empty:
            fig = px.bar(weekly, x="week", y=["calories", "protein", "fat", "carbs"], barmode="group")
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col5:
        st.markdown("**Adherence (last 7 days)**")
        cal_adh = calorie_adherence(dm, cal_target, window=7)
        prot_adh = protein_adherence(dm, prot_target, window=7)
        adh_df = pd.DataFrame({
            "Metric": ["Calorie adherence", "Protein adherence"],
            "Score": [cal_adh * 100, prot_adh * 100],
        })
        fig = px.bar(adh_df, x="Metric", y="Score", text_auto=".0f", range_y=[0, 100])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)


# ── Progress Dashboard ───────────────────────────────────────────────────────

def render_progress_dashboard():
    st.subheader("Progress Dashboard")
    goals = get_user_goals(st.session_state.username)
    goal_type = goals["goal_type"] if goals else "fat_loss"
    cal_target = float(goals["calorie_target"]) if goals and goals["calorie_target"] else 0
    prot_target = float(goals["protein_target"]) if goals and goals["protein_target"] else 0
    train_target = int(goals["training_days_per_week"]) if goals and goals["training_days_per_week"] else 4

    conn = get_db_connection()
    sessions = load_sessions(conn, st.session_state.username, days=60)
    sets_df = load_sets_with_exercises(conn, st.session_state.username, days=60)
    dm = daily_macros(conn, st.session_state.username, days=30)
    food_adh = food_logging_adherence(conn, st.session_state.username, window=7)
    conn.close()

    work_adh = workout_adherence(sessions, train_target, window_weeks=1)
    cal_adh = calorie_adherence(dm, cal_target, window=7)
    prot_adh = protein_adherence(dm, prot_target, window=7)
    hs = weekly_hard_sets_per_muscle(sets_df, weeks=1)

    t_score = training_score(work_adh, hs)
    n_score = nutrition_score(cal_adh, prot_adh, goal_type)
    c_score = consistency_score(work_adh, food_adh)

    col1, col2, col3 = st.columns(3)
    col1.metric("Training score", f"{t_score}/100")
    col2.metric("Nutrition score", f"{n_score}/100")
    col3.metric("Consistency score", f"{c_score}/100")

    st.markdown("---")

    st.markdown("**PRs this month**")
    prs = prs_this_month(sets_df)
    if not prs.empty:
        st.dataframe(prs, use_container_width=True)
    else:
        st.caption("No PR data yet — keep training!")

    st.markdown("---")
    st.markdown("**Recommendations**")
    tips = generate_recommendations(
        goal_type=goal_type,
        daily_macros_df=dm,
        calorie_target=cal_target,
        protein_target=prot_target,
        sessions_df=sessions,
        training_days_target=train_target,
        hard_sets_df=hs,
    )
    for tip in tips:
        st.info(f"**{tip['category']}:** {tip['message']}")


# ── Body Progress ────────────────────────────────────────────────────────────

def render_body_progress():
    st.subheader("Body Progress")

    tab1, tab2, tab3 = st.tabs(["Log weight / waist", "Upload photo", "Gallery & trends"])

    with tab1:
        bp_date = st.date_input("Date", value=datetime.today(), key="bp_date")
        bp_weight = st.number_input("Body weight (kg)", min_value=0.0, step=0.1, key="bp_weight")
        bp_waist = st.number_input("Waist (cm) — optional", min_value=0.0, step=0.5, value=0.0, key="bp_waist")

        if st.button("Save body metrics", key="bp_save"):
            if bp_weight <= 0:
                st.warning("Enter a valid weight.")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO body_metrics (user, date, weight_kg, waist_cm) VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE weight_kg = VALUES(weight_kg), waist_cm = VALUES(waist_cm)
                """, (st.session_state.username, bp_date, bp_weight, bp_waist if bp_waist > 0 else None))
                conn.commit()
                conn.close()
                st.success("Saved!")

    with tab2:
        photo_date = st.date_input("Photo date", value=datetime.today(), key="ph_date")
        photo_notes = st.text_input("Notes", key="ph_notes")
        uploaded = st.file_uploader("Upload a body photo", type=["jpg", "jpeg", "png"], key="ph_up")

        if uploaded and st.button("Save photo", key="ph_save"):
            upload_dir = os.path.join("uploads", st.session_state.username)
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{photo_date}_{uploaded.name}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, "wb") as f:
                f.write(uploaded.getbuffer())
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO body_photos (user, taken_date, file_path, notes) VALUES (%s, %s, %s, %s)",
                (st.session_state.username, photo_date, filepath, photo_notes or None),
            )
            conn.commit()
            conn.close()
            st.success("Photo saved!")

    with tab3:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT date, weight_kg, waist_cm FROM body_metrics WHERE user = %s ORDER BY date",
            (st.session_state.username,),
        )
        bm = pd.DataFrame(cursor.fetchall())
        if not bm.empty:
            st.markdown("**Weight trend**")
            fig = px.line(bm, x="date", y="weight_kg", markers=True)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

            waist_data = bm[bm["waist_cm"].notna() & (bm["waist_cm"] > 0)]
            if not waist_data.empty:
                st.markdown("**Waist trend**")
                fig2 = px.line(waist_data, x="date", y="waist_cm", markers=True)
                fig2.update_layout(height=300)
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No body metrics logged yet.")

        cursor.execute(
            "SELECT taken_date, file_path, notes FROM body_photos WHERE user = %s ORDER BY taken_date DESC LIMIT 20",
            (st.session_state.username,),
        )
        photos = cursor.fetchall()
        conn.close()

        if photos:
            st.markdown("**Photos**")
            for p in photos:
                if os.path.exists(p["file_path"]):
                    st.image(p["file_path"], caption=f"{p['taken_date']} — {p['notes'] or ''}", width=300)
        else:
            st.caption("No photos uploaded yet.")


# ── Health Report (unchanged) ────────────────────────────────────────────────

class Health_Report:
    def __init__(self):
        st.title("Health-Report PDF Processor")
        uploaded = st.file_uploader("Upload one PDF", type="pdf")
        if not uploaded:
            st.stop()
        tmpdir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmpdir, uploaded.name)
        with open(tmp_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.info(f"Saved to temporary file: `{tmp_path}`")

        if st.button("Extract parameters"):
            with st.spinner("Running AI extraction…"):
                try:
                    context = asyncio.run(extract_context_from_pdf(tmpdir))
                    st.success(f"Extracted Context={context.model_dump()}")
                    params_new = report_parameters_extractor(tmp_path, "")

                    processed_out_path = f"HealthReport/{st.session_state.username}/processed_report/{context.date}/report_{context.name}_{context.date}.json"
                    processed_dir_name = os.path.dirname(processed_out_path)
                    os.makedirs(processed_dir_name, exist_ok=True)
                    processed_parameter_dict = {"context": context.model_dump(), "params": params_new}
                    with open(processed_out_path, "w") as f:
                        json.dump(processed_parameter_dict, f, indent=4)
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
                    st.stop()
            datastore_dir = "./datastore"
            os.makedirs(datastore_dir, exist_ok=True)
            dest = os.path.join(datastore_dir, uploaded.name)
            shutil.move(tmp_path, dest)
            st.success(f"Moved PDF to datastore: `{dest}`")


# ──────────────────────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────────────────────

def Register(user, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user = %s", (user,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return False, "User already exists."
    cursor.execute("INSERT INTO users (user, password, role) VALUES (%s, %s, %s)", (user, password, role))
    conn.commit()
    conn.close()
    return True, "User registered successfully."


def Auth(user, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user = %s AND password = %s", (user, password))
    user_data = cursor.fetchall()
    conn.commit()
    conn.close()
    return user_data[0] if user_data else None


def auth_client():
    if st.session_state.get("logged_in"):
        st.sidebar.write(f"Logged in as: {st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
        return True

    action = st.sidebar.radio("Action", ["Login", "Register"])
    if action == "Login":
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            auth_result = Auth(username, password)
            if auth_result and auth_result[3] in ['admin', 'user']:
                st.success(f"Logged in as {username} with role: {auth_result[3]}")
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = auth_result[3]
            else:
                st.error("Invalid username or password")
    else:
        reg_username = st.text_input("Choose a username", key="reg_username")
        reg_password = st.text_input("Choose a password", type="password", key="reg_password")
        reg_password2 = st.text_input("Confirm password", type="password", key="reg_password2")
        reg_role = st.selectbox("Select role", ["user"], key="reg_role")
        if st.button("Register", key="register_button"):
            if reg_password != reg_password2:
                st.error("Passwords do not match")
            else:
                success, msg = Register(reg_username, reg_password, reg_role)
                if success:
                    st.success(msg)
                    st.info("You can now log in with your credentials.")
                else:
                    st.error(msg)
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    setup_database()
    st.title("Health Tracker App")

    if not auth_client():
        return

    tabs = [
        "Log Workout",
        "Food Intake",
        "Water Intake",
        "Body Progress",
        "Workout Dashboard",
        "Nutrition Dashboard",
        "Progress Dashboard",
        "Goals & Settings",
        "View Last 1 Month Data",
        "Metrices",
        "Health Report",
    ]
    if st.session_state.get("role") == "admin":
        tabs.append("Admin: Exercises")

    tab = st.sidebar.selectbox("Choose a Tab", tabs)

    if tab == "Log Workout":
        render_workout_log()

    elif tab == "Food Intake":
        FoodTab(tab_name="Food Intake")

    elif tab == "Water Intake":
        WaterIntakeTab()

    elif tab == "Body Progress":
        render_body_progress()

    elif tab == "Workout Dashboard":
        render_workout_dashboard()

    elif tab == "Nutrition Dashboard":
        render_nutrition_dashboard()

    elif tab == "Progress Dashboard":
        render_progress_dashboard()

    elif tab == "Goals & Settings":
        render_goals()

    elif tab == "View Last 1 Month Data":
        st.header("View Last 1 Month Data")
        food_intake, water_intake = fetch_last_month_data()

        st.subheader("Food Intake")
        if not food_intake.empty:
            st.dataframe(food_intake)
        else:
            st.write("No food intake records found for the last 1 month.")

        st.subheader("Water Intake")
        if not water_intake.empty:
            st.dataframe(water_intake)
        else:
            st.write("No water intake records found for the last 1 month.")

    elif tab == "Metrices":
        st.header("View your progress")
        agg_perDay_perMeal, agg_perDay = calculate_metrices()

        st.subheader("agg_perDay_perMeal")
        st.dataframe(agg_perDay_perMeal)
        st.subheader("agg_perDay")
        st.dataframe(agg_perDay)

        st.title("Nutritional Data Visualization")
        st.sidebar.header("Visualization Options")
        dataset = st.sidebar.selectbox("Choose a dataset:", ["Daily Aggregates", "Meal-wise Aggregates"])
        chart_type = st.sidebar.selectbox("Choose a chart type:", ["Bar", "Line"])

        if dataset == "Daily Aggregates":
            st.subheader("Daily Aggregates")
            metric = st.selectbox("Choose a metric:", ["total_protein_per_day", "total_fat_per_day", "total_calories_per_day"])
            if chart_type == "Bar":
                fig = px.bar(agg_perDay, x="date", y=metric, title=f"{metric} Over Days")
            elif chart_type == "Line":
                fig = px.line(agg_perDay, x="date", y=metric, title=f"{metric} Over Days")
            st.plotly_chart(fig)

        elif dataset == "Meal-wise Aggregates":
            st.subheader("Meal-wise Aggregates")
            metric = st.selectbox("Choose a metric:", ["total_protein_per_meal", "total_fat_per_meal", "total_calories_per_meal"])
            meal_types = st.multiselect("Select meal types to view:", agg_perDay_perMeal["meal_type"].unique(), default=agg_perDay_perMeal["meal_type"].unique())
            if meal_types:
                filtered_data = agg_perDay_perMeal[agg_perDay_perMeal["meal_type"].isin(meal_types)]
                if chart_type == "Bar":
                    fig = px.bar(filtered_data, x="date", y=metric, color="meal_type", title=f"{metric} for Selected Meal Types Over Days")
                elif chart_type == "Line":
                    fig = px.line(filtered_data, x="date", y=metric, color="meal_type", title=f"{metric} for Selected Meal Types Over Days")
                st.plotly_chart(fig)
            else:
                st.warning("Please select at least one meal type to display the data.")

    elif tab == "Health Report":
        Health_Report()

    elif tab == "Admin: Exercises":
        render_admin_exercises()


if __name__ == "__main__":
    main()
