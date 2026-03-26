import os
from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

from backend.db import get_conn
from backend.auth_utils import get_current_user

router = APIRouter()


class BodyMetricsCreate(BaseModel):
    date: str
    weight_kg: float
    waist_cm: Optional[float] = None


@router.post("/metrics")
def save_body_metrics(body: BodyMetricsCreate, user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO body_metrics (user, date, weight_kg, waist_cm) VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE weight_kg=VALUES(weight_kg), waist_cm=VALUES(waist_cm)
        """, (user["username"], body.date, body.weight_kg, body.waist_cm))
        conn.commit()
        return {"message": "Saved"}


@router.get("/metrics")
def get_body_metrics(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT date, weight_kg, waist_cm FROM body_metrics WHERE user=%s ORDER BY date",
            (user["username"],),
        )
        return cursor.fetchall()


@router.post("/photos")
async def upload_photo(
    taken_date: str = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", user["username"])
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{taken_date}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO body_photos (user, taken_date, file_path, notes) VALUES (%s,%s,%s,%s)",
            (user["username"], taken_date, f"/uploads/{user['username']}/{filename}", notes or None),
        )
        conn.commit()
        return {"message": "Photo saved", "path": f"/uploads/{user['username']}/{filename}"}


@router.get("/photos")
def get_photos(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, taken_date, file_path, notes FROM body_photos WHERE user=%s ORDER BY taken_date DESC LIMIT 30",
            (user["username"],),
        )
        return cursor.fetchall()
