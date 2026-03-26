"""Core AI trainer orchestration service.

Handles:
- System prompt construction with user memories
- Conversation history loading / persistence
- OpenAI streaming chat completions with tool-call loop
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any

from openai import OpenAI

from backend.db import get_conn
from backend.services.trainer_memory import load_memories
from backend.services.trainer_tools import TOOL_DEFINITIONS, execute_tool

MODEL = os.getenv("TRAINER_MODEL", "gpt-4o-mini")
HISTORY_LIMIT = 30  # max messages loaded for context
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()  # uses OPENAI_API_KEY env var
    return _client


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_PERSONA = """\
You are an expert fitness trainer and nutrition coach inside the Health Tracker app.

Your capabilities:
- View the user's goals, workout history, nutrition data, body metrics, and exercise catalog using your tools.
- Propose changes to goals, workout plans, and food logs. These appear as action cards the user can confirm or reject — never silently modify data.
- Remember important long-term context about the user (injuries, preferences, schedule, experience) by calling save_memory.

Guidelines:
- Be encouraging, evidence-based, and concise.
- When the user asks you to plan a workout or set goals, ALWAYS look up their data first so your suggestions are personalised.
- When proposing a workout, use real exercise IDs from the catalog. If you're unsure which exercises exist, call get_exercise_catalog first.
- For goal setting, ask clarifying questions about the user's experience, schedule, and preferences before proposing.
- When logging food, ALWAYS break meals into individual food items and estimate calories, protein, fat, and carbs for each item. Never log a composite meal as a single entry.
- Use metric units (kg, cm) unless the user specifies otherwise.
- Keep responses focused — no walls of text.
- Today's date is {today}.
"""


def _build_system_prompt(username: str) -> str:
    memories = load_memories(username)
    prompt = _PERSONA.format(today=date.today().isoformat())

    if memories:
        prompt += "\n## What you remember about this user:\n"
        for m in memories:
            ts = m["created_at"]
            if isinstance(ts, datetime):
                ts = ts.strftime("%Y-%m-%d")
            prompt += f"- [{m['category']}] {m['content']} (saved {ts})\n"

    return prompt


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------


def load_history(username: str) -> list[dict]:
    """Load recent chat messages for the OpenAI messages array."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT role, content, tool_calls, action_data
            FROM chat_messages
            WHERE user=%s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (username, HISTORY_LIMIT),
        )
        rows = cur.fetchall()

    rows.reverse()
    messages: list[dict] = []
    for r in rows:
        msg: dict[str, Any] = {"role": r["role"], "content": r["content"] or ""}
        if r["tool_calls"]:
            tc = r["tool_calls"] if isinstance(r["tool_calls"], list) else json.loads(r["tool_calls"])
            msg["tool_calls"] = tc
            if not msg["content"]:
                msg["content"] = None
        messages.append(msg)
    return messages


def save_message(username: str, role: str, content: str | None, tool_calls: Any = None, action_data: Any = None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages (user, role, content, tool_calls, action_data) VALUES (%s,%s,%s,%s,%s)",
            (
                username,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                json.dumps(action_data, default=_json_serial) if action_data else None,
            ),
        )
        conn.commit()


def clear_history(username: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_messages WHERE user=%s", (username,))
        conn.commit()


def get_history_for_display(username: str, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, role, content, action_data, created_at
            FROM chat_messages
            WHERE user=%s AND role IN ('user', 'assistant')
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (username, limit),
        )
        rows = cur.fetchall()
    rows.reverse()
    result = []
    for r in rows:
        entry: dict[str, Any] = {
            "id": r["id"],
            "role": r["role"],
            "content": r["content"] or "",
            "created_at": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else str(r["created_at"]),
        }
        if r["action_data"]:
            entry["action_data"] = r["action_data"] if isinstance(r["action_data"], dict) else json.loads(r["action_data"])
        result.append(entry)
    return result


def _json_serial(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ---------------------------------------------------------------------------
# Streaming chat with tool-call loop
# ---------------------------------------------------------------------------

_STATUS_MAP = {
    "get_user_profile": "Looking at your profile and goals...",
    "get_workout_history": "Reviewing your recent workouts...",
    "get_nutrition_summary": "Checking your nutrition data...",
    "get_exercise_catalog": "Browsing the exercise catalog...",
    "get_body_metrics": "Checking your body metrics...",
    "propose_goal_update": "Preparing goal suggestion...",
    "propose_workout_plan": "Building a workout plan for you...",
    "propose_food_log": "Preparing food log entry...",
    "save_memory": "Saving that to memory...",
}


def stream_chat(username: str, user_message: str):
    """
    Generator that yields SSE event dicts:
      {"event": "text", "data": "token..."}
      {"event": "status", "data": "Looking at your workouts..."}
      {"event": "action", "data": {action_id, action_type, display_data}}
      {"event": "done", "data": ""}
    """
    save_message(username, "user", user_message)

    system_prompt = _build_system_prompt(username)
    history = load_history(username)

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append(h)

    client = _get_client()
    collected_actions: list[dict] = []

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            stream=True,
        )

        assistant_text = ""
        tool_calls_acc: dict[int, dict] = {}
        finish_reason = None

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

            if delta.content:
                assistant_text += delta.content
                yield {"event": "text", "data": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {
                            "id": tc.id or "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    if tc.id:
                        tool_calls_acc[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_acc[idx]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_acc[idx]["function"]["arguments"] += tc.function.arguments

        if finish_reason == "tool_calls" and tool_calls_acc:
            sorted_tcs = [tool_calls_acc[i] for i in sorted(tool_calls_acc.keys())]

            assistant_msg: dict[str, Any] = {"role": "assistant", "content": assistant_text or None, "tool_calls": sorted_tcs}
            messages.append(assistant_msg)

            for tc in sorted_tcs:
                fn_name = tc["function"]["name"]
                yield {"event": "status", "data": _STATUS_MAP.get(fn_name, f"Running {fn_name}...")}

                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                result_str, action = execute_tool(fn_name, fn_args, username)

                if action:
                    collected_actions.append(action)
                    yield {"event": "action", "data": json.dumps(action)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })

            continue

        # No more tool calls — we're done
        break

    save_message(
        username,
        "assistant",
        assistant_text,
        action_data=collected_actions if collected_actions else None,
    )

    yield {"event": "done", "data": ""}
