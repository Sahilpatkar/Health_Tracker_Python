from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional

from backend.db import get_conn
from backend.auth_utils import get_current_user, require_admin

router = APIRouter()


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: str
    equipment: str = "other"


class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
def list_active(muscle_group: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        if muscle_group and muscle_group != "All":
            cursor.execute(
                "SELECT id, name, muscle_group, equipment FROM exercises WHERE is_active=1 AND muscle_group=%s ORDER BY name",
                (muscle_group,),
            )
        else:
            cursor.execute("SELECT id, name, muscle_group, equipment FROM exercises WHERE is_active=1 ORDER BY name")
        return cursor.fetchall()


@router.get("/all")
def list_all(admin: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exercises ORDER BY name")
        return cursor.fetchall()


@router.post("")
def create(body: ExerciseCreate, admin: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO exercises (name, muscle_group, equipment) VALUES (%s,%s,%s)",
                (body.name.strip(), body.muscle_group, body.equipment),
            )
            conn.commit()
            return {"id": cursor.lastrowid, "message": "Created"}
        except Exception:
            raise HTTPException(status_code=409, detail="Exercise name already exists")


@router.put("/{exercise_id}")
def update(exercise_id: int, body: ExerciseUpdate, admin: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.cursor()
        fields, values = [], []
        if body.name is not None:
            fields.append("name=%s"); values.append(body.name.strip())
        if body.muscle_group is not None:
            fields.append("muscle_group=%s"); values.append(body.muscle_group)
        if body.equipment is not None:
            fields.append("equipment=%s"); values.append(body.equipment)
        if body.is_active is not None:
            fields.append("is_active=%s"); values.append(1 if body.is_active else 0)
        if not fields:
            return {"message": "Nothing to update"}
        values.append(exercise_id)
        try:
            cursor.execute(f"UPDATE exercises SET {', '.join(fields)} WHERE id=%s", values)
            conn.commit()
            return {"message": "Updated"}
        except Exception:
            raise HTTPException(status_code=409, detail="Exercise name already exists")


@router.delete("/{exercise_id}")
def delete(exercise_id: int, admin: dict = Depends(require_admin)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM exercise_sets WHERE exercise_id=%s", (exercise_id,))
        if cursor.fetchone()[0] > 0:
            raise HTTPException(status_code=409, detail="Cannot delete — sets reference this exercise. Deactivate instead.")
        cursor.execute("DELETE FROM exercises WHERE id=%s", (exercise_id,))
        conn.commit()
        return {"message": "Deleted"}
