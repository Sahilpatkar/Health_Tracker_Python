import os
import json
import mysql.connector
import requests
import streamlit as st
from typing import Optional, Dict
from openai import OpenAI
from duckduckgo_search import DDGS

# Read database config from Streamlit secrets
DB_CONFIG = {
    "host": st.secrets["database_docker"]["host"],
    "port": st.secrets["database_docker"]["port"],
    "user": st.secrets["database_docker"]["user"],
    "password": st.secrets["database_docker"]["password"],
    "database": st.secrets["database_docker"]["database"],
}

openai_client = OpenAI()

SYSTEM_PROMPT = (
    "You are a helpful nutrition assistant."
    " Ask the user questions to gather the date, meal type, food item and quantity."
    " Once you have all fields, call the 'insert_food' tool to save the record." 
    " Use the 'get_macros' tool when you need macronutrients for a food item." 
    " If macros are missing, you may use the web to search."
)


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_macros_from_db(food_item: str) -> Optional[Dict[str, float]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, serving_size, protein, fat, calories FROM food_items WHERE food_item = %s",
        (food_item,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "food_id": row[0],
            "serving_size": row[1],
            "protein": row[2],
            "fat": row[3],
            "calories": row[4],
        }
    return None


def fetch_macros_from_web(food_item: str) -> Optional[Dict[str, float]]:
    """Use a simple web API or search engine to fetch macros."""
    try:
        url = f"https://api.calorieninjas.com/v1/nutrition?query={food_item}"
        headers = {"X-Api-Key": os.getenv("CALORIE_NINJAS_API_KEY", "")}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("items", [])
            if data:
                item = data[0]
                return {
                    "food_id": None,
                    "serving_size": "100 g",
                    "protein": item.get("protein_g", 0.0),
                    "fat": item.get("fat_total_g", 0.0),
                    "calories": item.get("calories", 0.0),
                }
    except Exception:
        pass

    # fall back to duckduckgo search
    try:
        with DDGS() as ddgs:
            results = ddgs.text(f"{food_item} calories protein fat per 100g", max_results=1)
            for r in results:
                snippet = r.get("body", "")
                # naive extraction of numbers
                nums = [float(x) for x in snippet.split() if x.replace(".", "", 1).isdigit()]
                if len(nums) >= 3:
                    return {
                        "food_id": None,
                        "serving_size": "100 g",
                        "protein": nums[1],
                        "fat": nums[2],
                        "calories": nums[0],
                    }
    except Exception:
        pass
    return None


def insert_food_intake(food_id: Optional[int], date: str, meal_type: str, food_item: str, quantity: float, unit: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_intake (user, food_id, date, meal_type, food_item, quantity, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (st.session_state.username, food_id, date, meal_type, food_item, quantity, unit),
    )
    conn.commit()
    conn.close()
    return "Entry saved"


def get_macros_tool(food_item: str) -> Dict[str, float]:
    macros = fetch_macros_from_db(food_item)
    if macros is None:
        macros = fetch_macros_from_web(food_item)
    return macros or {}


def insert_food_tool(date: str, meal_type: str, food_item: str, quantity: float) -> str:
    macros = get_macros_tool(food_item)
    if macros.get("food_id") is None:
        food_id = None
        unit = macros.get("serving_size", "100 g")
    else:
        food_id = macros["food_id"]
        unit = macros["serving_size"]
    return insert_food_intake(food_id, date, meal_type, food_item, quantity, unit)


def run_agent(messages):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_macros",
                "description": "Return macronutrients for the given food item",
                "parameters": {
                    "type": "object",
                    "properties": {"food_item": {"type": "string"}},
                    "required": ["food_item"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "insert_food",
                "description": "Insert a food intake record into the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "meal_type": {"type": "string"},
                        "food_item": {"type": "string"},
                        "quantity": {"type": "number"},
                    },
                    "required": ["date", "meal_type", "food_item", "quantity"],
                },
            },
        },
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message
    if message.tool_calls:
        for call in message.tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
            if func_name == "get_macros":
                result = get_macros_tool(**args)
            elif func_name == "insert_food":
                result = insert_food_tool(**args)
            else:
                result = "Unknown tool"
            messages.append({"role": "assistant", "tool_calls": [call], "content": None})
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
            return run_agent(messages)

    return message.content


class FoodChatBot:
    def __init__(self):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        reply = run_agent(self.messages)
        self.messages.append({"role": "assistant", "content": reply})
        return reply
