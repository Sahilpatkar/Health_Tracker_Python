from fastapi import APIRouter, Depends, Query
from typing import Optional

from backend.db import get_conn
from backend.auth_utils import require_admin

router = APIRouter()


@router.get("/users")
def list_users(admin: dict = Depends(require_admin)):
    """List all registered users (no passwords returned)."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT userId, user, role FROM users ORDER BY userId")
        return cursor.fetchall()


@router.get("/users/{username}/food")
def user_food(username: str, date: Optional[str] = Query(None), admin: dict = Depends(require_admin)):
    """View a user's food intake. Optionally filter by date (YYYY-MM-DD)."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        if date:
            cursor.execute(
                "SELECT * FROM food_intake WHERE user=%s AND date=%s ORDER BY id",
                (username, date),
            )
        else:
            cursor.execute(
                "SELECT * FROM food_intake WHERE user=%s ORDER BY date DESC, id LIMIT 100",
                (username,),
            )
        return cursor.fetchall()


@router.get("/users/{username}/workouts")
def user_workouts(username: str, admin: dict = Depends(require_admin)):
    """View a user's recent workout sessions with exercise sets."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM workout_sessions WHERE user=%s ORDER BY session_date DESC LIMIT 30",
            (username,),
        )
        sessions = cursor.fetchall()
        for s in sessions:
            cursor.execute(
                "SELECT es.*, e.name AS exercise_name, e.muscle_group "
                "FROM exercise_sets es JOIN exercises e ON es.exercise_id = e.id "
                "WHERE es.session_id=%s ORDER BY es.set_order",
                (s["id"],),
            )
            s["sets"] = cursor.fetchall()
        return sessions


@router.get("/users/{username}/goals")
def user_goals(username: str, admin: dict = Depends(require_admin)):
    """View a user's nutrition/training goals."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_goals WHERE user=%s", (username,))
        return cursor.fetchone()


@router.get("/users/{username}/metrics")
def user_metrics(username: str, admin: dict = Depends(require_admin)):
    """View a user's body metrics (weight, waist) over time."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM body_metrics WHERE user=%s ORDER BY date DESC LIMIT 90",
            (username,),
        )
        return cursor.fetchall()


@router.get("/users/{username}/water")
def user_water(username: str, admin: dict = Depends(require_admin)):
    """View a user's water intake history."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM water_intake WHERE user=%s ORDER BY date DESC LIMIT 30",
            (username,),
        )
        return cursor.fetchall()


@router.get("/users/{username}/photos")
def user_photos(username: str, admin: dict = Depends(require_admin)):
    """View a user's body progress photo metadata."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, taken_date, file_path, notes FROM body_photos WHERE user=%s ORDER BY taken_date DESC LIMIT 50",
            (username,),
        )
        return cursor.fetchall()


@router.get("/users/{username}/chat")
def user_chat(username: str, admin: dict = Depends(require_admin)):
    """View a user's AI trainer chat history (most recent first)."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, role, content, tool_calls, action_data, created_at FROM chat_messages "
            "WHERE user=%s ORDER BY created_at DESC LIMIT 200",
            (username,),
        )
        return cursor.fetchall()


@router.get("/users/{username}/memory")
def user_memory(username: str, admin: dict = Depends(require_admin)):
    """View stored trainer memory entries for a user."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, category, content, created_at FROM trainer_memory WHERE user=%s ORDER BY created_at DESC",
            (username,),
        )
        return cursor.fetchall()


@router.get("/users/{username}/pending-actions")
def user_pending_actions(username: str, admin: dict = Depends(require_admin)):
    """View pending/confirmed AI trainer actions for a user."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, action_type, payload, status, created_at FROM pending_actions "
            "WHERE user=%s ORDER BY created_at DESC LIMIT 100",
            (username,),
        )
        return cursor.fetchall()


@router.get("/summary")
def platform_summary(admin: dict = Depends(require_admin)):
    """High-level stats: total users, workouts, food logs, etc."""
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        stats = {}
        for table, label in [
            ("users", "total_users"),
            ("workout_sessions", "total_workouts"),
            ("food_intake", "total_food_logs"),
            ("water_intake", "total_water_logs"),
            ("body_metrics", "total_body_metrics"),
            ("chat_messages", "total_chat_messages"),
        ]:
            cursor.execute(f"SELECT COUNT(*) AS cnt FROM {table}")
            stats[label] = cursor.fetchone()["cnt"]
        return stats
