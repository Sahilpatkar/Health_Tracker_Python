"""OpenAI function-calling tool definitions and executors for the AI trainer."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from backend.db import get_conn
from backend.services.trainer_memory import save_memory as _persist_memory

# ---------------------------------------------------------------------------
# OpenAI tool schemas (function-calling format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Get the user's current goals, latest body metrics, and training preferences.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_workout_history",
            "description": "Get the user's recent workout sessions with exercise names, sets, reps, and weights.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to look back. Default 30.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutrition_summary",
            "description": "Get the user's daily macro intake (calories, protein, fat, carbs) and water intake for recent days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to look back. Default 14.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exercise_catalog",
            "description": "List available exercises, optionally filtered by muscle group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "muscle_group": {
                        "type": "string",
                        "description": "Filter by muscle group (e.g. 'chest', 'back', 'legs'). Omit for all.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_body_metrics",
            "description": "Get the user's body weight and waist measurement trend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days. Default 60.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_goal_update",
            "description": (
                "Propose updating the user's fitness goals. The user must confirm before "
                "changes are applied. Always explain your reasoning to the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_type": {
                        "type": "string",
                        "enum": ["fat_loss", "muscle_gain", "maintenance", "recomp"],
                    },
                    "calorie_target": {"type": "number"},
                    "protein_target": {"type": "number"},
                    "carb_target": {"type": "number"},
                    "fat_target": {"type": "number"},
                    "training_days_per_week": {"type": "integer"},
                },
                "required": ["goal_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_workout_plan",
            "description": (
                "Propose a workout session for the user. The user must confirm before "
                "it is saved. Include exercise names, sets, reps, and suggested weight."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_date": {
                        "type": "string",
                        "description": "Date for the session in YYYY-MM-DD format.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional session notes (e.g. 'Push day').",
                    },
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "exercise_id": {"type": "integer"},
                                "exercise_name": {"type": "string"},
                                "sets": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "reps": {"type": "integer"},
                                            "weight": {"type": "number"},
                                        },
                                        "required": ["reps"],
                                    },
                                },
                            },
                            "required": ["exercise_id", "exercise_name", "sets"],
                        },
                    },
                },
                "required": ["session_date", "exercises"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_food_log",
            "description": (
                "Propose logging food intake. ALWAYS break a meal into individual "
                "food items (e.g. 'chicken curry, rice, dal' becomes 3 separate items). "
                "Estimate calories, protein, fat, and carbs for each item based on "
                "the quantity provided. The user must confirm before it is saved."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "meal_type": {
                        "type": "string",
                        "enum": ["breakfast", "lunch", "dinner", "snack"],
                    },
                    "items": {
                        "type": "array",
                        "description": "Each distinct food item in the meal, with estimated macros.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "food_item": {"type": "string", "description": "Name of the individual food item."},
                                "quantity": {"type": "number", "description": "Amount consumed."},
                                "unit": {"type": "string", "description": "Unit of measurement (e.g. g, ml, pieces, cups)."},
                                "calories": {"type": "number", "description": "Estimated calories (kcal) for this quantity."},
                                "protein": {"type": "number", "description": "Estimated protein in grams."},
                                "fat": {"type": "number", "description": "Estimated fat in grams."},
                                "carbs": {"type": "number", "description": "Estimated carbs in grams."},
                            },
                            "required": ["food_item", "quantity", "unit", "calories", "protein", "fat", "carbs"],
                        },
                    },
                },
                "required": ["date", "meal_type", "items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": (
                "Save an important piece of context about the user that should be "
                "remembered across sessions (e.g. injuries, dietary restrictions, "
                "schedule preferences, experience level). Use this proactively when "
                "the user shares relevant long-term information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "injury",
                            "preference",
                            "limitation",
                            "medical",
                            "schedule",
                            "experience",
                            "other",
                        ],
                    },
                    "content": {
                        "type": "string",
                        "description": "A concise description of the fact to remember.",
                    },
                },
                "required": ["category", "content"],
            },
        },
    },
]


def _json_serial(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _to_json(data: Any) -> str:
    return json.dumps(data, default=_json_serial)


# ---------------------------------------------------------------------------
# Tool executors — each returns (result_str, optional_action_dict)
# action_dict is non-None only for propose_* tools
# ---------------------------------------------------------------------------


def execute_tool(name: str, arguments: dict, username: str) -> tuple[str, dict | None]:
    """Dispatch a tool call and return (result_text, pending_action_or_none)."""
    executor = _EXECUTORS.get(name)
    if not executor:
        return f"Unknown tool: {name}", None
    return executor(arguments, username)


def _get_user_profile(args: dict, username: str) -> tuple[str, None]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM user_goals WHERE user=%s", (username,))
        goals = cur.fetchone()

        cur.execute(
            "SELECT * FROM body_metrics WHERE user=%s ORDER BY date DESC LIMIT 5",
            (username,),
        )
        metrics = cur.fetchall()

    return _to_json({"goals": goals, "recent_body_metrics": metrics}), None


def _get_workout_history(args: dict, username: str) -> tuple[str, None]:
    days = args.get("days", 30)
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT ws.id, ws.session_date, ws.notes,
                   e.name AS exercise_name, e.muscle_group,
                   es.set_order, es.reps, es.weight, es.rpe, es.rir
            FROM workout_sessions ws
            JOIN exercise_sets es ON es.session_id = ws.id
            JOIN exercises e ON e.id = es.exercise_id
            WHERE ws.user=%s AND ws.session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY ws.session_date DESC, ws.id, es.set_order
            """,
            (username, days),
        )
        rows = cur.fetchall()
    return _to_json(rows), None


def _get_nutrition_summary(args: dict, username: str) -> tuple[str, None]:
    days = args.get("days", 14)
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT fi.date, fi.meal_type, fi.food_item, fi.quantity, fi.unit,
                   COALESCE(fit.calories, fi.calories) AS calories,
                   COALESCE(fit.protein, fi.protein)   AS protein,
                   COALESCE(fit.fat, fi.fat)           AS fat,
                   COALESCE(fit.carbs, fi.carbs, 0)    AS carbs
            FROM food_intake fi
            LEFT JOIN food_items fit ON fit.food_item = fi.food_item
            WHERE fi.user=%s AND fi.date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY fi.date DESC
            """,
            (username, days),
        )
        food = cur.fetchall()

        cur.execute(
            """
            SELECT date, water_intake FROM water_intake
            WHERE user=%s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY date DESC
            """,
            (username, days),
        )
        water = cur.fetchall()

    return _to_json({"food_intake": food, "water_intake": water}), None


def _get_exercise_catalog(args: dict, username: str) -> tuple[str, None]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        if args.get("muscle_group"):
            cur.execute(
                "SELECT id, name, muscle_group, equipment FROM exercises WHERE is_active=1 AND muscle_group=%s ORDER BY name",
                (args["muscle_group"],),
            )
        else:
            cur.execute(
                "SELECT id, name, muscle_group, equipment FROM exercises WHERE is_active=1 ORDER BY muscle_group, name"
            )
        rows = cur.fetchall()
    return _to_json(rows), None


def _get_body_metrics(args: dict, username: str) -> tuple[str, None]:
    days = args.get("days", 60)
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT date, weight_kg, waist_cm FROM body_metrics WHERE user=%s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) ORDER BY date",
            (username, days),
        )
        rows = cur.fetchall()
    return _to_json(rows), None


def _propose_goal_update(args: dict, username: str) -> tuple[str, dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pending_actions (user, action_type, payload) VALUES (%s, %s, %s)",
            (username, "update_goals", json.dumps(args)),
        )
        conn.commit()
        action_id = cur.lastrowid

    action = {
        "action_id": action_id,
        "action_type": "update_goals",
        "display_data": args,
    }
    return _to_json({"status": "proposed", "action_id": action_id}), action


def _propose_workout_plan(args: dict, username: str) -> tuple[str, dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pending_actions (user, action_type, payload) VALUES (%s, %s, %s)",
            (username, "create_workout", json.dumps(args, default=_json_serial)),
        )
        conn.commit()
        action_id = cur.lastrowid

    action = {
        "action_id": action_id,
        "action_type": "create_workout",
        "display_data": args,
    }
    return _to_json({"status": "proposed", "action_id": action_id}), action


def _propose_food_log(args: dict, username: str) -> tuple[str, dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pending_actions (user, action_type, payload) VALUES (%s, %s, %s)",
            (username, "log_food", json.dumps(args)),
        )
        conn.commit()
        action_id = cur.lastrowid

    action = {
        "action_id": action_id,
        "action_type": "log_food",
        "display_data": args,
    }
    return _to_json({"status": "proposed", "action_id": action_id}), action


def _save_memory(args: dict, username: str) -> tuple[str, None]:
    _persist_memory(username, args["category"], args["content"])
    return _to_json({"status": "saved", "category": args["category"]}), None


_EXECUTORS = {
    "get_user_profile": _get_user_profile,
    "get_workout_history": _get_workout_history,
    "get_nutrition_summary": _get_nutrition_summary,
    "get_exercise_catalog": _get_exercise_catalog,
    "get_body_metrics": _get_body_metrics,
    "propose_goal_update": _propose_goal_update,
    "propose_workout_plan": _propose_workout_plan,
    "propose_food_log": _propose_food_log,
    "save_memory": _save_memory,
}


# ---------------------------------------------------------------------------
# Action confirmation executors
# ---------------------------------------------------------------------------


def confirm_action(action_id: int, username: str) -> dict:
    """Execute a pending action after user confirmation."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM pending_actions WHERE id=%s AND user=%s AND status='pending'",
            (action_id, username),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Action not found or already processed"}

        payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
        action_type = row["action_type"]

        if action_type == "update_goals":
            _execute_goal_update(cur, username, payload)
        elif action_type == "create_workout":
            _execute_create_workout(cur, username, payload)
        elif action_type == "log_food":
            _execute_log_food(cur, username, payload)

        cur.execute(
            "UPDATE pending_actions SET status='confirmed' WHERE id=%s",
            (action_id,),
        )
        conn.commit()

    return {"status": "confirmed", "action_type": action_type}


def reject_action(action_id: int, username: str) -> dict:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE pending_actions SET status='rejected' WHERE id=%s AND user=%s AND status='pending'",
            (action_id, username),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"error": "Action not found or already processed"}
    return {"status": "rejected"}


def _execute_goal_update(cur, username: str, payload: dict):
    cur.execute(
        """
        INSERT INTO user_goals (user, goal_type, calorie_target, protein_target, carb_target, fat_target, training_days_per_week)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            goal_type=VALUES(goal_type), calorie_target=VALUES(calorie_target),
            protein_target=VALUES(protein_target), carb_target=VALUES(carb_target),
            fat_target=VALUES(fat_target), training_days_per_week=VALUES(training_days_per_week)
        """,
        (
            username,
            payload.get("goal_type", "fat_loss"),
            payload.get("calorie_target", 0),
            payload.get("protein_target", 0),
            payload.get("carb_target", 0),
            payload.get("fat_target", 0),
            payload.get("training_days_per_week", 4),
        ),
    )


def _execute_create_workout(cur, username: str, payload: dict):
    cur.execute(
        "INSERT INTO workout_sessions (user, session_date, notes) VALUES (%s,%s,%s)",
        (username, payload["session_date"], payload.get("notes")),
    )
    session_id = cur.lastrowid
    set_order = 1
    for ex in payload.get("exercises", []):
        for s in ex.get("sets", []):
            cur.execute(
                """
                INSERT INTO exercise_sets (session_id, exercise_id, set_order, reps, weight)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (session_id, ex["exercise_id"], set_order, s["reps"], s.get("weight", 0)),
            )
            set_order += 1


def _execute_log_food(cur, username: str, payload: dict):
    items = payload.get("items", [payload])
    for item in items:
        cur.execute(
            "SELECT id FROM food_items WHERE food_item = %s",
            (item["food_item"],),
        )
        row = cur.fetchone()
        food_id = row[0] if row else None

        cur.execute(
            """
            INSERT INTO food_intake
              (user, food_id, date, meal_type, food_item, quantity, unit,
               calories, protein, fat, carbs)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                username,
                food_id,
                payload["date"],
                payload["meal_type"],
                item.get("food_item", item.get("food_item")),
                item.get("quantity"),
                item.get("unit"),
                item.get("calories"),
                item.get("protein"),
                item.get("fat"),
                item.get("carbs"),
            ),
        )
