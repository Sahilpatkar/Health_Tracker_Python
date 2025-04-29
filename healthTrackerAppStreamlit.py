import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px

# Database Configuration
db_config = st.secrets["database_local"]



DB_CONFIG = {
    "host": db_config["host"],
    "port": db_config["port"],
    "user": db_config["user"],
    "password": db_config["password"],
    "database": db_config["database"],
}

# Database Connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Initialize Database
def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()


    # Create user table
    # cursor.execute("""
    #     DROP TABLE IF EXISTS users
    #
    # """)

    # Create user table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userId INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(255) NOT NULL
        )
    """)

    # Add users
    # cursor.execute("""
    #     INSERT INTO users (user, password, role)
    #     VALUES ('Sahil', '123456', 'admin'),
    #             ('Rahul','123456','admin')
    # """)


    # Create food_intake table
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
            user VARCHAR(255),
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
        INSERT INTO food_intake (user, food_id, date, meal_type, food_item, quantity, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (st.session_state.username, food_id, date, meal_type, food_item, quantity, unit))
    conn.commit()
    conn.close()

# Insert Data into water_intake
def insert_water_intake(date, water_intake):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO water_intake (user, date, water_intake)
        VALUES (%s, %s, %s)
    """, (st.session_state.username, date, water_intake))
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

def calculate_metrices():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # # Total Agg of all macros per Day Per Meal
    cursor.execute("""
        with user_table as (
        select * from food_intake
                 where user = %s
        )
        select date,F1.meal_type, SUM(quantity*protein) as total_protein_per_meal, SUM(quantity*fat) as total_fat_per_meal, SUM(quantity*calories) as total_calories_per_meal
        from user_table F1
        join food_items F2 on F1.food_id = F2.id
        group by date,F1.meal_type
        """,(st.session_state.username,))
    agg_perDay_perMeal = pd.DataFrame(cursor.fetchall())

    # Total Agg of all macros per Day
    cursor.execute("""
            with user_table as (
            select * from food_intake
                     where user = %s
        )

        select date, SUM(total_protein_per_meal) as total_protein_per_day, SUM(total_fat_per_meal) as total_fat_per_day, SUM(total_calories_per_meal) as total_calories_per_day
        from(select date,F1.meal_type, SUM(quantity*protein) as total_protein_per_meal, SUM(quantity*fat) as total_fat_per_meal, SUM(quantity*calories) as total_calories_per_meal
        from user_table F1
        join food_items F2 on F1.food_id = F2.id
        group by date,F1.meal_type) table1
        group by date;
        """,(st.session_state.username,))
    agg_perDay = pd.DataFrame(cursor.fetchall())

    conn.close()

    return agg_perDay_perMeal, agg_perDay

# Food Tab
class FoodTab:
    def __init__(self, tab_name):
        self.tab_name = tab_name
        
        st.subheader(f"Log your food intake")

        self.selected_meal_type = st.selectbox("Select meal type", ["Breakfast","Morning Snacks","Lunch","Evening Snacks","Dinner"])

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
            delete_last_entry(self.date, self.selected_meal_type)
            st.success(f"Deleted the last {self.selected_meal_type} entry for {self.date}.")
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



def Register(user, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE user = %s", (user,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return False, "User already exists."
    # Insert new user (ensure you hash the password in production)
    cursor.execute("INSERT INTO users (user, password, role) VALUES (%s, %s, %s)", (user, password, role))
    conn.commit()
    conn.close()
    return True, "User registered successfully."


def Auth(user, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
            SELECT * FROM users WHERE user = %s AND password = %s
        """, (user, password))
    user_data = cursor.fetchall()
    conn.commit()
    conn.close()
    if user_data:
        return user_data[0]
    else:
        return None

def auth_client():
    # If already logged in, show logout button and user details.
    if st.session_state.get("logged_in"):
        st.sidebar.write(f"Logged in as: {st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            #st.experimental_rerun()
        return True

    # If not logged in, allow the user to choose between Login and Register.
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
                #st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    else:  # Registration
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


# Main Streamlit App
def main():
    setup_database()
    st.title("Health Tracker App")

    if auth_client():


        # Select Tab
        tab = st.sidebar.selectbox("Choose a Tab", ["Food Intake",  "Water Intake", "View Last 1 Month Data","Metrices"])

        if tab == "Food Intake":
            FoodTab(tab_name="Food Intake")  # Adjust meal type as needed
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

        elif tab == "Metrices":
            st.header("View your progress")

            agg_perDay_perMeal,agg_perDay = calculate_metrices()

            st.subheader("agg_perDay_perMeal")
            st.dataframe(agg_perDay_perMeal)

            st.subheader("agg_perDay")
            st.dataframe(agg_perDay)

            # Streamlit App
            st.title("Nutritional Data Visualization")

            # Sidebar Options
            st.sidebar.header("Visualization Options")
            dataset = st.sidebar.selectbox("Choose a dataset:", ["Daily Aggregates", "Meal-wise Aggregates"])
            chart_type = st.sidebar.selectbox("Choose a chart type:", ["Bar", "Line"])

            if dataset == "Daily Aggregates":
                st.subheader("Daily Aggregates")
                metric = st.selectbox("Choose a metric:", ["total_protein_per_day", "total_fat_per_day", "total_calories_per_day"])

                # Create the appropriate chart
                if chart_type == "Bar":
                    fig = px.bar(agg_perDay, x="date", y=metric, title=f"{metric} Over Days", labels={"date": "Date", metric: "Value"})
                elif chart_type == "Line":
                    fig = px.line(agg_perDay, x="date", y=metric, title=f"{metric} Over Days", labels={"date": "Date", metric: "Value"})

                st.plotly_chart(fig)

            elif dataset == "Meal-wise Aggregates":
                st.subheader("Meal-wise Aggregates")
                metric = st.selectbox("Choose a metric:", ["total_protein_per_meal", "total_fat_per_meal", "total_calories_per_meal"])
                meal_types = st.multiselect("Select meal types to view:", agg_perDay_perMeal["meal_type"].unique(), default=agg_perDay_perMeal["meal_type"].unique())

                if meal_types:
                    # Filter the DataFrame based on selected meal types
                    filtered_data = agg_perDay_perMeal[agg_perDay_perMeal["meal_type"].isin(meal_types)]

                    # Create the appropriate chart
                    if chart_type == "Bar":
                        fig = px.bar(
                            filtered_data,
                            x="date",
                            y=metric,
                            color="meal_type",
                            title=f"{metric} for Selected Meal Types Over Days",
                            labels={"date": "Date", metric: "Value"}
                        )
                    elif chart_type == "Line":
                        fig = px.line(
                            filtered_data,
                            x="date",
                            y=metric,
                            color="meal_type",
                            title=f"{metric} for Selected Meal Types Over Days",
                            labels={"date": "Date", metric: "Value"}
                        )

                    st.plotly_chart(fig)
                else:
                    st.warning("Please select at least one meal type to display the data.")


if __name__ == "__main__":
    main()
