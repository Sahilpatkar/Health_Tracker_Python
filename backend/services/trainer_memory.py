"""Persistent memory system for the AI trainer.

Stores important cross-session context about each user (injuries, preferences,
schedule, experience level, etc.) with a per-user cap to keep the system prompt
bounded.
"""

from __future__ import annotations

from backend.db import get_conn

MAX_MEMORIES_PER_USER = 30


def load_memories(username: str) -> list[dict]:
    """Fetch all memories for injection into the system prompt."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, category, content, created_at FROM trainer_memory WHERE user=%s ORDER BY created_at",
            (username,),
        )
        return cur.fetchall()


def get_memories(username: str) -> list[dict]:
    """Public-facing list of memories (same as load but explicit intent)."""
    return load_memories(username)


def save_memory(username: str, category: str, content: str) -> int:
    """Save a new memory, enforcing the per-user cap by deleting the oldest."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM trainer_memory WHERE user=%s", (username,))
        count = cur.fetchone()[0]

        if count >= MAX_MEMORIES_PER_USER:
            overflow = count - MAX_MEMORIES_PER_USER + 1
            cur.execute(
                "DELETE FROM trainer_memory WHERE user=%s ORDER BY created_at ASC LIMIT %s",
                (username, overflow),
            )

        cur.execute(
            "INSERT INTO trainer_memory (user, category, content) VALUES (%s, %s, %s)",
            (username, category, content),
        )
        conn.commit()
        return cur.lastrowid


def delete_memory(username: str, memory_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM trainer_memory WHERE id=%s AND user=%s",
            (memory_id, username),
        )
        conn.commit()
        return cur.rowcount > 0
