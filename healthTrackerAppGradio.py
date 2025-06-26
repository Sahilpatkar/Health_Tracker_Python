# New Gradio front-end for Health Tracker
import os
import tempfile
import asyncio
import json
from datetime import datetime, timedelta
import mysql.connector
import pandas as pd
import plotly.express as px
import gradio as gr

from Agents.HealthReport_InformationAgent import extract_context_from_pdf
from medical_extractor_project.main import report_parameters_extractor

# Database Configuration - reuse from streamlit secrets if available
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "healthtracker"),
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Database setup and helper functions copied from Streamlit app

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            userId INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(255) NOT NULL
        )
        """
    )
    cursor.execute(
        """
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
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS food_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_item VARCHAR(255) NOT NULL,
            serving_size VARCHAR(255) NOT NULL,
            protein FLOAT NOT NULL,
            fat FLOAT NOT NULL,
            calories FLOAT NOT NULL,
            UNIQUE (food_item)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS water_intake (
            user VARCHAR(255),
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            water_intake FLOAT NOT NULL,
            UNIQUE (date)
        )
        """
    )
    conn.commit()
    conn.close()


def get_food_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, food_item, serving_size FROM food_items")
    items = cursor.fetchall()
    conn.close()
    return items


def insert_food_intake(user, food_id, date, meal_type, food_item, quantity, unit):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_intake (user, food_id, date, meal_type, food_item, quantity, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user, food_id, date, meal_type, food_item, quantity, unit),
    )
    conn.commit()
    conn.close()


def insert_water_intake(user, date, water_intake):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO water_intake (user, date, water_intake)
        VALUES (%s, %s, %s)
        """,
        (user, date, water_intake),
    )
    conn.commit()
    conn.close()


def delete_last_entry(user, date, meal_type=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if meal_type:
        cursor.execute(
            """
            DELETE FROM food_intake WHERE user=%s AND date=%s AND meal_type=%s ORDER BY id DESC LIMIT 1
            """,
            (user, date, meal_type),
        )
    else:
        cursor.execute(
            """
            DELETE FROM water_intake WHERE user=%s AND date=%s ORDER BY id DESC LIMIT 1
            """,
            (user, date),
        )
    conn.commit()
    conn.close()


def fetch_last_month_data(user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    one_month_ago = datetime.today() - timedelta(days=30)

    cursor.execute(
        """
        SELECT * FROM food_intake WHERE user=%s AND date >= %s ORDER BY date DESC
        """,
        (user, one_month_ago),
    )
    food_intake = pd.DataFrame(cursor.fetchall())

    cursor.execute(
        """
        SELECT * FROM water_intake WHERE user=%s AND date >= %s ORDER BY date DESC
        """,
        (user, one_month_ago),
    )
    water_intake = pd.DataFrame(cursor.fetchall())
    conn.close()
    return food_intake, water_intake


def calculate_metrics(user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        WITH user_table AS (
            SELECT * FROM food_intake WHERE user=%s
        )
        SELECT date,F1.meal_type, SUM(quantity*protein) AS total_protein_per_meal,
               SUM(quantity*fat) AS total_fat_per_meal,
               SUM(quantity*calories) AS total_calories_per_meal
        FROM user_table F1
        JOIN food_items F2 ON F1.food_id = F2.id
        GROUP BY date,F1.meal_type
        """,
        (user,),
    )
    agg_perDay_perMeal = pd.DataFrame(cursor.fetchall())

    cursor.execute(
        """
        WITH user_table AS (
            SELECT * FROM food_intake WHERE user=%s
        )
        SELECT date,
               SUM(total_protein_per_meal) AS total_protein_per_day,
               SUM(total_fat_per_meal) AS total_fat_per_day,
               SUM(total_calories_per_meal) AS total_calories_per_day
        FROM (
            SELECT date,F1.meal_type, SUM(quantity*protein) AS total_protein_per_meal,
                   SUM(quantity*fat) AS total_fat_per_meal,
                   SUM(quantity*calories) AS total_calories_per_meal
            FROM user_table F1
            JOIN food_items F2 ON F1.food_id = F2.id
            GROUP BY date,F1.meal_type
        ) table1
        GROUP BY date
        """,
        (user,),
    )
    agg_perDay = pd.DataFrame(cursor.fetchall())
    conn.close()
    return agg_perDay_perMeal, agg_perDay


def Register(user, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user=%s", (user,))
    if cursor.fetchone():
        conn.close()
        return False, "User already exists"
    cursor.execute(
        "INSERT INTO users (user, password, role) VALUES (%s, %s, %s)",
        (user, password, role),
    )
    conn.commit()
    conn.close()
    return True, "User registered successfully"


def Auth(user, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE user=%s AND password=%s",
        (user, password),
    )
    user_data = cursor.fetchone()
    conn.close()
    return user_data

# -------------------- Gradio Interface --------------------

setup_database()


def login_fn(username, password, state):
    user_data = Auth(username, password)
    if user_data:
        state["logged_in"] = True
        state["user"] = username
        return f"Logged in as {username}", gr.update(visible=True), gr.update(visible=False)
    else:
        return "Invalid credentials", gr.update(), gr.update()


def register_fn(username, password, confirm, state):
    if password != confirm:
        return "Passwords do not match"
    success, msg = Register(username, password, "user")
    return msg


def add_food(meal_type, food_item, quantity, date, state):
    if not state.get("logged_in"):
        return "Please login first"
    items = {f[1]: (f[0], f[2]) for f in get_food_items()}
    if food_item not in items:
        return "Invalid food item"
    food_id, serving = items[food_item]
    insert_food_intake(state["user"], food_id, date, meal_type, food_item, quantity, serving)
    return f"Added {food_item}"


def delete_food(meal_type, date, state):
    if not state.get("logged_in"):
        return "Please login first"
    delete_last_entry(state["user"], date, meal_type)
    return "Deleted last entry"


def add_water(water, date, state):
    if not state.get("logged_in"):
        return "Please login first"
    insert_water_intake(state["user"], date, water)
    return "Added water intake"


def delete_water(date, state):
    if not state.get("logged_in"):
        return "Please login first"
    delete_last_entry(state["user"], date)
    return "Deleted water intake entry"


def show_month_data(state):
    if not state.get("logged_in"):
        return None, None
    food_df, water_df = fetch_last_month_data(state["user"])
    return food_df, water_df


def show_metrics(state):
    if not state.get("logged_in"):
        return None, None, None
    per_meal, per_day = calculate_metrics(state["user"])
    fig = px.bar(per_day, x="date", y="total_calories_per_day", title="Calories per Day")
    return per_meal, per_day, fig


def process_pdf(file, state):
    if not state.get("logged_in"):
        return "Please login first"
    if file is None:
        return "No file uploaded"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, file.name)
        file.save(tmp_path)
        context = asyncio.run(extract_context_from_pdf(tmpdir))
        params = report_parameters_extractor(tmp_path, "")
        out_dir = f"HealthReport/{state['user']}/processed_report/{context.date}"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"report_{context.name}_{context.date}.json")
        with open(out_path, "w") as f:
            json.dump({"context": context.model_dump(), "params": params}, f, indent=4)
    return f"Processed report saved to {out_path}"


with gr.Blocks() as demo:
    state = gr.State({"logged_in": False, "user": ""})

    gr.Markdown("# Health Tracker - Gradio")

    with gr.Tab("Login"):
        login_username = gr.Textbox(label="Username")
        login_password = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_msg = gr.Markdown()
        login_btn.click(login_fn, [login_username, login_password, state], [login_msg, gr.TabGroup.update(), gr.TabGroup.update()])

    with gr.Tab("Register"):
        reg_username = gr.Textbox(label="Username")
        reg_password = gr.Textbox(label="Password", type="password")
        reg_confirm = gr.Textbox(label="Confirm Password", type="password")
        reg_btn = gr.Button("Register")
        reg_msg = gr.Markdown()
        reg_btn.click(register_fn, [reg_username, reg_password, reg_confirm, state], reg_msg)

    with gr.Tab("Food Intake"):
        meal_type = gr.Dropdown(["Breakfast", "Morning Snacks", "Lunch", "Evening Snacks", "Dinner"], label="Meal Type")
        food_item = gr.Dropdown([f[1] for f in get_food_items()], label="Food Item")
        quantity = gr.Number(label="Quantity", value=1.0)
        date_input = gr.Textbox(label="Date (YYYY-MM-DD)", value=datetime.today().strftime("%Y-%m-%d"))
        add_food_btn = gr.Button("Add")
        del_food_btn = gr.Button("Delete Last Entry")
        food_msg = gr.Markdown()
        add_food_btn.click(add_food, [meal_type, food_item, quantity, date_input, state], food_msg)
        del_food_btn.click(delete_food, [meal_type, date_input, state], food_msg)

    with gr.Tab("Water Intake"):
        water_date = gr.Textbox(label="Date (YYYY-MM-DD)", value=datetime.today().strftime("%Y-%m-%d"))
        water_amount = gr.Number(label="Water (L)")
        add_water_btn = gr.Button("Add")
        del_water_btn = gr.Button("Delete")
        water_msg = gr.Markdown()
        add_water_btn.click(add_water, [water_amount, water_date, state], water_msg)
        del_water_btn.click(delete_water, [water_date, state], water_msg)

    with gr.Tab("Last Month Data"):
        view_btn = gr.Button("Refresh")
        food_df = gr.Dataframe()
        water_df = gr.Dataframe()
        view_btn.click(show_month_data, state, [food_df, water_df])

    with gr.Tab("Metrics"):
        metric_btn = gr.Button("Calculate")
        per_meal_df = gr.Dataframe()
        per_day_df = gr.Dataframe()
        plot = gr.Plot()
        metric_btn.click(show_metrics, state, [per_meal_df, per_day_df, plot])

    with gr.Tab("Health Report"):
        pdf_file = gr.File(label="Upload PDF")
        process_btn = gr.Button("Process")
        pdf_msg = gr.Markdown()
        process_btn.click(process_pdf, [pdf_file, state], pdf_msg)

if __name__ == "__main__":
    demo.launch()
