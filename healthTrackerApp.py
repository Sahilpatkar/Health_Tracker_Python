import tkinter as tk
from tkinter import ttk
from datetime import datetime
import mysql.connector
import pandas as pd

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "3305",
    "user": "root",
    "password": "123456",
    "database": "healthtracker"
}

# Database Setup
def setup_database():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create health_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
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

    # Populate food_items table from Excel if updated
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
        required_columns = ["food item", "serving size (100 g)", "protein", "fat"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: '{col}' in the Excel file.")

        # Rename columns to match the database field names
        df.rename(columns={
            "food item": "Food Item",
            "serving size (100 g)": "Serving Size",
            "protein": "Protein",
            "fat": "Fat"
        }, inplace=True)

        df = df.astype({"Protein": float, "Fat": float})  # Ensure correct data types

        # Fetch existing food items from the database
        cursor.execute("SELECT food_item, serving_size, protein, fat FROM food_items")
        existing_items = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

        for _, row in df.iterrows():
            food_item = row["Food Item"]
            serving_size = row["Serving Size"]
            protein = row["Protein"]
            fat = row["Fat"]

            # Check if the record exists and needs updating
            if (food_item not in existing_items or
                existing_items[food_item] != (serving_size, protein, fat)):
                cursor.execute("""
                    INSERT INTO food_items (food_item, serving_size, protein, fat)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    serving_size = VALUES(serving_size),
                    protein = VALUES(protein),
                    fat = VALUES(fat)
                """, (food_item, serving_size, protein, fat))

        conn.commit()
    except Exception as e:
        print(f"Error updating food items from Excel: {e}")

setup_database()

# Base Tab Class
class BaseTab:
    def __init__(self, parent, tab_name):
        self.tab = ttk.Frame(parent)
        parent.add(self.tab, text=tab_name)

        self.date_label = ttk.Label(self.tab, text="Date (YYYY-MM-DD):")
        self.date_label.pack(pady=5)
        self.date_var = tk.StringVar()
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(self.tab, textvariable=self.date_var)
        self.date_entry.pack(pady=5)

# Food Tab
class FoodTab(BaseTab):
    def __init__(self, parent, tab_name, meal_type):
        super().__init__(parent, tab_name)
        self.meal_type = meal_type

        self.food_label = ttk.Label(self.tab, text="Select Food Item:")
        self.food_label.pack(pady=5)

        self.food_var = tk.StringVar()
        self.food_dropdown = ttk.Combobox(self.tab, textvariable=self.food_var, state="readonly")
        self.load_food_items()
        self.food_dropdown.pack(pady=5)

        self.unit_label = ttk.Label(self.tab, text="Serving Size:")
        self.unit_label.pack(pady=5)
        self.unit_var = tk.StringVar()
        self.unit_entry = ttk.Entry(self.tab, textvariable=self.unit_var, state="readonly")
        self.unit_entry.pack(pady=5)

        self.quantity_label = ttk.Label(self.tab, text="Quantity:")
        self.quantity_label.pack(pady=5)
        self.quantity_entry = ttk.Entry(self.tab)
        self.quantity_entry.pack(pady=5)

        self.save_button = ttk.Button(self.tab, text="Save", command=self.save_data)
        self.save_button.pack(pady=10)

        self.delete_button = ttk.Button(self.tab, text="Delete Previous Entry", command=self.delete_last_entry)
        self.delete_button.pack(pady=10)

        self.session_entries_label = ttk.Label(self.tab, text="Session Entries:")
        self.session_entries_label.pack(pady=5)
        self.session_entries = tk.Text(self.tab, height=10, state="disabled")
        self.session_entries.pack(pady=5)

        self.food_dropdown.bind("<<ComboboxSelected>>", self.update_unit)

    def load_food_items(self):
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT food_item FROM food_items")
        food_items = [row[0] for row in cursor.fetchall()]
        self.food_dropdown["values"] = food_items
        conn.close()

    def update_unit(self, event):
        selected_food = self.food_var.get()
        if selected_food:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT serving_size FROM food_items WHERE food_item = %s", (selected_food,))
            self.unit_var.set(cursor.fetchone()[0])
            conn.close()

    def save_data(self):
        date = self.date_var.get()
        food_item = self.food_var.get()
        quantity = self.quantity_entry.get()
        unit = self.unit_var.get()

        if date and food_item and quantity:
            try:
                quantity = float(quantity)
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO health_data (date, meal_type, food_item, quantity, unit)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (date, self.meal_type, food_item, quantity, unit),
                )
                conn.commit()

                # Log the entry in the session log
                self.log_session_entry(f"{date}: {self.meal_type} - {food_item} ({quantity} {unit})")

                conn.close()
                self.quantity_entry.delete(0, tk.END)
                tk.messagebox.showinfo("Success", f"{self.meal_type} data updated successfully!")
            except ValueError:
                tk.messagebox.showwarning("Error", "Please enter a valid number for quantity!")
        else:
            tk.messagebox.showwarning("Error", "Please fill in all fields!")

    def delete_last_entry(self):
        date = self.date_var.get()
        if date:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM health_data WHERE id = (SELECT MAX(id) from health_data WHERE date = %s AND meal_type = %s)", (date, self.meal_type))
            conn.commit()
            conn.close()
            tk.messagebox.showinfo("Success", f"Last {self.meal_type} entry deleted successfully!")

            # Clear the session log for this meal type
            self.session_entries.configure(state="normal")
            self.session_entries.delete(1.0, tk.END)
            self.session_entries.configure(state="disabled")
        else:
            tk.messagebox.showwarning("Error", "Please select a date!")

    def log_session_entry(self, entry):
        self.session_entries.configure(state="normal")
        self.session_entries.insert(tk.END, entry + "\n")
        self.session_entries.configure(state="disabled")

# Water Intake Tab
class WaterIntakeTab(BaseTab):
    def __init__(self, parent, tab_name):
        super().__init__(parent, tab_name)

        self.water_label = ttk.Label(self.tab, text="Water Intake (L):")
        self.water_label.pack(pady=5)
        self.water_entry = ttk.Entry(self.tab)
        self.water_entry.pack(pady=5)

        self.save_button = ttk.Button(self.tab, text="Save", command=self.save_data)
        self.save_button.pack(pady=10)

        self.delete_button = ttk.Button(self.tab, text="Delete Previous Entry", command=self.delete_last_entry)
        self.delete_button.pack(pady=10)

        self.session_entries_label = ttk.Label(self.tab, text="Session Entries:")
        self.session_entries_label.pack(pady=5)
        self.session_entries = tk.Text(self.tab, height=10, state="disabled")
        self.session_entries.pack(pady=5)

    def save_data(self):
        date = self.date_var.get()
        water_intake = self.water_entry.get()

        if date and water_intake:
            try:
                water_intake = float(water_intake)
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO water_intake (date, water_intake)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                    water_intake = VALUES(water_intake)
                    """,
                    (date, water_intake),
                )
                conn.commit()

                # Log the entry in the session log
                self.log_session_entry(f"{date}: Water Intake - {water_intake} L")

                conn.close()
                self.water_entry.delete(0, tk.END)
                tk.messagebox.showinfo("Success", "Water intake data updated successfully!")
            except ValueError:
                tk.messagebox.showwarning("Error", "Please enter a valid number for water intake!")
        else:
            tk.messagebox.showwarning("Error", "Please fill in all fields!")

    def delete_last_entry(self):
        date = self.date_var.get()
        if date:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM water_intake WHERE date = %s", (date,))
            conn.commit()
            conn.close()
            tk.messagebox.showinfo("Success", "Last water intake entry deleted successfully!")

            # Clear the session log for water intake
            self.session_entries.configure(state="normal")
            self.session_entries.delete(1.0, tk.END)
            self.session_entries.configure(state="disabled")
        else:
            tk.messagebox.showwarning("Error", "Please select a date!")

    def log_session_entry(self, entry):
        self.session_entries.configure(state="normal")
        self.session_entries.insert(tk.END, entry + "\n")
        self.session_entries.configure(state="disabled")

# Main Application
class HealthTrackerApp:
    def __init__(self, root):
        root.title("Health Tracker App")
        root.geometry("400x600")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.breakfast_tab = FoodTab(self.notebook, "Breakfast", "Breakfast")
        self.lunch_tab = FoodTab(self.notebook, "Lunch", "Lunch")
        self.dinner_tab = FoodTab(self.notebook, "Dinner", "Dinner")
        self.water_tab = WaterIntakeTab(self.notebook, "Water Intake")

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthTrackerApp(root)
    root.mainloop()
