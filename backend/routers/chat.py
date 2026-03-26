"""Chat router — SSE streaming endpoint, action confirmation, history & memory management."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.auth_utils import get_current_user
from backend.services.trainer import (
    clear_history,
    get_history_for_display,
    save_message,
    stream_chat,
)
from backend.services.trainer_memory import delete_memory, get_memories
from backend.services.trainer_tools import confirm_action, reject_action

router = APIRouter()


class ChatMessage(BaseModel):
    content: str


class ActionRequest(BaseModel):
    action_id: int


def _sse_generator(username: str, user_message: str):
    """Wrap the synchronous stream_chat generator into SSE text format."""
    for event in stream_chat(username, user_message):
        etype = event["event"]
        data = event["data"]
        if isinstance(data, dict):
            data = json.dumps(data)
        data_escaped = data.replace("\n", "\ndata: ")
        yield f"event: {etype}\ndata: {data_escaped}\n\n"


@router.post("/message")
def send_message(body: ChatMessage, user: dict = Depends(get_current_user)):
    return StreamingResponse(
        _sse_generator(user["username"], body.content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
def chat_history(limit: int = 50, user: dict = Depends(get_current_user)):
    return get_history_for_display(user["username"], limit)


@router.delete("/history")
def delete_history(user: dict = Depends(get_current_user)):
    clear_history(user["username"])
    return {"message": "Chat history cleared"}


@router.post("/confirm-action")
def confirm(body: ActionRequest, user: dict = Depends(get_current_user)):
    result = confirm_action(body.action_id, user["username"])
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    save_message(
        user["username"],
        "assistant",
        f"Done! Your {result['action_type'].replace('_', ' ')} has been applied.",
    )
    return result


@router.post("/reject-action")
def reject(body: ActionRequest, user: dict = Depends(get_current_user)):
    result = reject_action(body.action_id, user["username"])
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    save_message(user["username"], "assistant", "No problem — I've discarded that suggestion.")
    return result


@router.get("/memories")
def list_memories(user: dict = Depends(get_current_user)):
    return get_memories(user["username"])


@router.delete("/memories/{memory_id}")
def remove_memory(memory_id: int, user: dict = Depends(get_current_user)):
    ok = delete_memory(user["username"], memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}
