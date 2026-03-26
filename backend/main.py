import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.db import setup_database
from backend.routers import admin, auth, exercises, workouts, food, goals, metrics, body, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(title="Health Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(exercises.router, prefix="/api/exercises", tags=["exercises"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["workouts"])
app.include_router(food.router, prefix="/api/food", tags=["food"])
app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(body.router, prefix="/api/body", tags=["body"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
