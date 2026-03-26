from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from backend.db import get_conn
from backend.auth_utils import get_current_user

router = APIRouter()


class GoalsUpdate(BaseModel):
    goal_type: str = "fat_loss"
    calorie_target: float = 0
    protein_target: float = 0
    carb_target: float = 0
    fat_target: float = 0
    training_days_per_week: int = 4


@router.get("")
def get_goals(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_goals WHERE user=%s", (user["username"],))
        row = cursor.fetchone()
        return row or {
            "goal_type": "fat_loss", "calorie_target": 2000, "protein_target": 120,
            "carb_target": 0, "fat_target": 0, "training_days_per_week": 4,
        }


@router.put("")
def update_goals(body: GoalsUpdate, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_goals (user, goal_type, calorie_target, protein_target, carb_target, fat_target, training_days_per_week)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                goal_type=VALUES(goal_type), calorie_target=VALUES(calorie_target),
                protein_target=VALUES(protein_target), carb_target=VALUES(carb_target),
                fat_target=VALUES(fat_target), training_days_per_week=VALUES(training_days_per_week)
        """, (user["username"], body.goal_type, body.calorie_target, body.protein_target,
              body.carb_target, body.fat_target, body.training_days_per_week))
        conn.commit()
        return {"message": "Goals saved"}
