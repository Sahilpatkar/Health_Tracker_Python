from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.db import get_conn
from backend.auth_utils import create_token, get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


@router.post("/login")
def login(body: LoginRequest):
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT userId, user, role FROM users WHERE user=%s AND password=%s",
            (body.username, body.password),
        )
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(row["user"], row["role"])
    return {"token": token, "username": row["user"], "role": row["role"]}


@router.post("/register")
def register(body: RegisterRequest):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT userId FROM users WHERE user=%s", (body.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="User already exists")
        cursor.execute(
            "INSERT INTO users (user, password, role) VALUES (%s,%s,%s)",
            (body.username, body.password, body.role),
        )
        conn.commit()
    return {"message": "Registered successfully"}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
