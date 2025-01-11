import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "3305",
    "user": "root",
    "password": "123456",
    "database": "healthtracker",
}

# Database Connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Initialize Database
def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create food_intake table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_intake (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_id INT,
            date DATE NOT NULL,
            meal_type VARCHAR(255) NOT NULL,
            food_item VARCHAR(255),
            quantity FLOAT,
            unit VARCHAR(255)
        )
    """)

    # Create food_items table
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

    # Create water_intake table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_intake (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            water_intake FLOAT NOT NULL,
            UNIQUE (date)
        )
    """)
    update_food_items_from_excel(cursor, conn)
    conn.commit()
    conn.close()

def update_food_items_from_excel(cursor, conn):
    try:
        # Load food items from an Excel file
        df = pd.read_excel("food_items.xlsx")  # Ensure this file exists in the same directory

        # Normalize column names to handle case sensitivity
        df.columns = [col.strip().lower() for col in df.columns]

        # Ensure required columns exist
        required_columns = ["food item", "serving size (100 g)", "protein", "fat", "calories"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: '{col}' in the Excel file.")

        # Rename columns to match the database field names
        df.rename(columns={
            "food item": "Food Item",
            "serving size (100 g)": "Serving Size",
            "protein": "Protein",
            "fat": "Fat",
            "calories": "Calories"
        }, inplace=True)

        df = df.astype({"Protein": float, "Fat": float, "Calories": float})  # Ensure correct data types

        # Fetch existing food items from the database
        cursor.execute("SELECT food_item, serving_size, protein, fat, calories FROM food_items")
        existing_items = {row[0]: (row[1], row[2], row[3], row[4]) for row in cursor.fetchall()}

        for _, row in df.iterrows():
            food_item = row["Food Item"]
            serving_size = row["Serving Size"]
            protein = row["Protein"]
            fat = row["Fat"]
            calories = row["Calories"]

            # Check if the record exists and needs updating
            if (food_item not in existing_items or
                existing_items[food_item] != (serving_size, protein, fat, calories)):
                cursor.execute("""
                    INSERT INTO food_items (food_item, serving_size, protein, fat, calories)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    serving_size = VALUES(serving_size),
                    protein = VALUES(protein),
                    fat = VALUES(fat),
                    calories = VALUES(calories)
                """, (food_item, serving_size, protein, fat, calories))

        conn.commit()
    except Exception as e:
        print(f"Error updating food items from Excel: {e}")



# Fetch Food Items
def get_food_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id ,food_item, serving_size FROM food_items")
    food_items = cursor.fetchall()
    conn.close()
    return food_items

# Insert Data into food_intake
def insert_food_intake(food_id, date, meal_type, food_item, quantity, unit):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO food_intake (food_id, date, meal_type, food_item, quantity, unit)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (food_id, date, meal_type, food_item, quantity, unit))
    conn.commit()
    conn.close()

# Insert Data into water_intake
def insert_water_intake(date, water_intake):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO water_intake (date, water_intake)
        VALUES (%s, %s)
    """, (date, water_intake))
    conn.commit()
    conn.close()

# Delete Last Entry
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
        cursor.execute("""
            DELETE FROM water_intake
            WHERE date = %s
        """, (date,))
    conn.commit()
    conn.close()

# Fetch Last 1-Month Data
def fetch_last_month_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    one_month_ago = datetime.today() - timedelta(days=30)

    # Fetch food_intake
    cursor.execute("""
        SELECT * FROM food_intake WHERE date >= %s ORDER BY date DESC
    """, (one_month_ago,))
    food_intake = pd.DataFrame(cursor.fetchall())

    # Fetch water_intake
    cursor.execute("""
        SELECT * FROM water_intake WHERE date >= %s ORDER BY date DESC
    """, (one_month_ago,))
    water_intake = pd.DataFrame(cursor.fetchall())

    conn.close()
    
    return food_intake, water_intake

# Food Tab
class FoodTab:
    def __init__(self, tab_name):
        self.tab_name = tab_name
        
        st.subheader(f"Log your food intake")

        self.selected_meal_type = st.selectbox("Select meal type", ["Breakfast","Lunch","Dinner"])

        # Input Fields

        self.date = st.date_input("Date", value=datetime.today())
        self.food_items = get_food_items()
        self.selected_food_item = st.selectbox("Select Food Item", [f[1] for f in self.food_items])

        # Display Serving Size
        self.selected_food_info = next((f for f in self.food_items if f[1] == self.selected_food_item), None)
        self.serving_size = self.selected_food_info[2] if self.selected_food_info else "Unknown"
        self.food_id = self.selected_food_info[0] if self.selected_food_info else "Unknown"
        st.write(f"**Serving Size:** {self.serving_size}")
        st.write(f"**item id:** {self.food_id}")

        self.quantity = st.number_input("Quantity", min_value=0.0, step=0.1)

        # Save Button
        if st.button("Add Food"):
            self.save_data()

        # Delete Last Entry Button
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
            delete_last_entry(self.date, self.meal_type)
            st.success(f"Deleted the last {self.meal_type} entry for {self.date}.")
        else:
            st.warning("Please select a date.")

# Water Intake Tab
class WaterIntakeTab:
    def __init__(self):
        st.subheader("Log Your Water Intake")

        # Input Fields
        self.date = st.date_input("Date", value=datetime.today(), key="water_date")
        self.water_intake = st.number_input("Water Intake (L)", min_value=0.0, step=0.1)

        # Save Button
        if st.button("Add Water Intake"):
            self.save_data()

        # Delete Last Entry Button
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

# Main Streamlit App
def main():
    setup_database()
    st.title("Health Tracker App")

    # Select Tab
    tab = st.sidebar.selectbox("Choose a Tab", ["Food Intake",  "Water Intake", "View Last 1 Month Data"])

    if tab == "Food Intake":
        FoodTab(tab_name="Food Intake")  # Adjust meal type as needed
    # elif tab == "Food Intake - Lunch":
    #     FoodTab(tab_name="Food Intake", meal_type="Lunch")
    # elif tab == "Food Intake - Dinner":
    #     FoodTab(tab_name="Food Intake", meal_type="Dinner")
    elif tab == "Water Intake":
        WaterIntakeTab()
    elif tab == "View Last 1 Month Data":
        st.header("View Last 1 Month Data")

        # Fetch data
        food_intake, water_intake = fetch_last_month_data()
        print("TYPE",type(food_intake))

        # Display Health Data
        st.subheader("Food Intake")
        if not food_intake.empty:
            st.dataframe(food_intake)
        else:
            st.write("No food intake records found for the last 1 month.")

        # Display Water Intake Data
        st.subheader("Water Intake")
        if not water_intake.empty:
            st.dataframe(water_intake)
        else:
            st.write("No water intake records found for the last 1 month.")

if __name__ == "__main__":
    main()
