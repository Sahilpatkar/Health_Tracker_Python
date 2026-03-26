from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from backend.db import get_conn
from backend.auth_utils import get_current_user

router = APIRouter()


class FoodIntakeCreate(BaseModel):
    food_id: int
    date: str
    meal_type: str
    food_item: str
    quantity: float
    unit: str


class WaterIntakeCreate(BaseModel):
    date: str
    water_intake: float


@router.get("/items")
def list_food_items(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, food_item, serving_size, protein, fat, calories, COALESCE(carbs,0) as carbs FROM food_items ORDER BY food_item")
        return cursor.fetchall()


@router.post("/intake")
def add_food_intake(body: FoodIntakeCreate, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO food_intake (user, food_id, date, meal_type, food_item, quantity, unit)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (user["username"], body.food_id, body.date, body.meal_type, body.food_item, body.quantity, body.unit))
        conn.commit()
        return {"id": cursor.lastrowid, "message": "Added"}


@router.delete("/intake/{intake_id}")
def delete_food_intake(intake_id: int, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM food_intake WHERE id=%s AND user=%s", (intake_id, user["username"]))
        conn.commit()
        return {"message": "Deleted"}


@router.get("/intake")
def list_food_intake(days: int = 30, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT fi.id, fi.user, fi.food_id, fi.date, fi.meal_type,
                   fi.food_item, fi.quantity, fi.unit,
                   COALESCE(fo.calories, fi.calories) AS calories,
                   COALESCE(fo.protein, fi.protein)   AS protein,
                   COALESCE(fo.fat, fi.fat)           AS fat,
                   COALESCE(fo.carbs, fi.carbs, 0)    AS carbs
            FROM food_intake fi
            LEFT JOIN food_items fo ON fi.food_id = fo.id
            WHERE fi.user=%s AND fi.date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY fi.date DESC
        """, (user["username"], days))
        return cursor.fetchall()


@router.post("/water")
def add_water(body: WaterIntakeCreate, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO water_intake (user, date, water_intake) VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE water_intake=VALUES(water_intake)
        """, (user["username"], body.date, body.water_intake))
        conn.commit()
        return {"message": "Saved"}


@router.delete("/water/{water_id}")
def delete_water(water_id: int, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM water_intake WHERE id=%s AND user=%s", (water_id, user["username"]))
        conn.commit()
        return {"message": "Deleted"}


@router.get("/water")
def list_water(days: int = 30, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM water_intake WHERE user=%s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY date DESC
        """, (user["username"], days))
        return cursor.fetchall()
