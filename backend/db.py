import os
import csv
import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager

import pandas as pd

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "user"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "healthtracker"),
}

_pool: pooling.MySQLConnectionPool | None = None


def get_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="ht_pool",
            pool_size=10,
            pool_reset_session=True,
            **DB_CONFIG,
        )
    return _pool


@contextmanager
def get_conn():
    conn = get_pool().get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (DB_CONFIG["database"], table, column),
    )
    return cursor.fetchone()[0] > 0


def setup_database():
    with get_conn() as conn:
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

        for col in ("calories", "protein", "fat", "carbs"):
            if not _column_exists(cursor, "food_intake", col):
                cursor.execute(f"ALTER TABLE food_intake ADD COLUMN {col} FLOAT DEFAULT NULL")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_intake (
                user VARCHAR(255),
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                water_intake FLOAT NOT NULL,
                UNIQUE (date)
            )
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user VARCHAR(255) NOT NULL,
                role ENUM('user','assistant','system','tool') NOT NULL,
                content TEXT,
                tool_calls JSON,
                action_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chat_user_created (user, created_at)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trainer_memory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user VARCHAR(255) NOT NULL,
                category ENUM('injury','preference','limitation','medical','schedule','experience','other') NOT NULL,
                content VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_memory_user (user)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_actions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user VARCHAR(255) NOT NULL,
                action_type ENUM('update_goals','create_workout','log_food','log_water') NOT NULL,
                payload JSON NOT NULL,
                status ENUM('pending','confirmed','rejected','expired') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_action_user_status (user, status)
            )
        """)

        conn.commit()
        _seed_exercises(cursor, conn)
        _seed_food_items(cursor, conn)


def _seed_exercises(cursor, conn):
    seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exercises_seed.csv")
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


def _seed_food_items(cursor, conn):
    xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "food_items.xlsx")
    if not os.path.exists(xlsx_path):
        return
    try:
        df = pd.read_excel(xlsx_path)
        df.columns = [col.strip().lower() for col in df.columns]
        required = ["food item", "serving size (100 g)", "protein", "fat", "calories"]
        for col in required:
            if col not in df.columns:
                return
        df.rename(columns={
            "food item": "Food Item", "serving size (100 g)": "Serving Size",
            "protein": "Protein", "fat": "Fat", "calories": "Calories",
        }, inplace=True)
        if "carbs" in [c.lower() for c in df.columns]:
            df.rename(columns={"carbs": "Carbs"}, inplace=True)
        else:
            df["Carbs"] = 0.0
        df = df.astype({"Protein": float, "Fat": float, "Calories": float, "Carbs": float})
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO food_items (food_item, serving_size, protein, fat, calories, carbs)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                serving_size=VALUES(serving_size), protein=VALUES(protein),
                fat=VALUES(fat), calories=VALUES(calories), carbs=VALUES(carbs)
            """, (row["Food Item"], row["Serving Size"], row["Protein"],
                  row["Fat"], row["Calories"], row["Carbs"]))
        conn.commit()
    except Exception as e:
        print(f"Error seeding food items: {e}")
