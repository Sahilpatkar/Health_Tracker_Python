from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from backend.db import get_conn
from backend.auth_utils import get_current_user

router = APIRouter()


class SetData(BaseModel):
    exercise_id: int
    reps: int
    weight: float = 0
    rpe: Optional[float] = None
    rir: Optional[int] = None


class WorkoutCreate(BaseModel):
    session_date: str
    notes: Optional[str] = None
    exercises: list[dict]


@router.post("")
def create_workout(body: WorkoutCreate, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO workout_sessions (user, session_date, notes) VALUES (%s,%s,%s)",
            (user["username"], body.session_date, body.notes),
        )
        session_id = cursor.lastrowid
        set_order = 1
        for ex in body.exercises:
            for s in ex.get("sets", []):
                cursor.execute("""
                    INSERT INTO exercise_sets (session_id, exercise_id, set_order, reps, weight, rpe, rir)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (session_id, ex["exercise_id"], set_order, s["reps"], s.get("weight", 0),
                      s.get("rpe"), s.get("rir")))
                set_order += 1
        conn.commit()
        return {"session_id": session_id, "message": "Workout saved"}


@router.get("/sessions")
def list_sessions(days: int = 60, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ws.id, ws.session_date, ws.notes,
                   COUNT(es.id) as total_sets
            FROM workout_sessions ws
            LEFT JOIN exercise_sets es ON es.session_id = ws.id
            WHERE ws.user=%s AND ws.session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY ws.id
            ORDER BY ws.session_date DESC
        """, (user["username"], days))
        return cursor.fetchall()
