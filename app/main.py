import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.routes.ai import router as ai_router

from app.routes import user
from app.routes import ticket
from app.routes.comment import router as comment_router


app = FastAPI(
    title="Support Ticket API",
    description="Backend API for managing customer support tickets",
    version="1.0.0"
)

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(user.router)
app.include_router(ticket.router)
app.include_router(comment_router)
app.include_router(ai_router)


@app.get("/health")
def home():
    return {
        "message": "Support Ticket API is running"
    }


@app.get("/db-test")
def db_test():
    try:
        with engine.connect():
            return {
                "message": "Database connection successful"
            }
    except Exception as e:
        return {
            "message": "Database connection failed",
            "error": str(e)
        }


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True),
    name="frontend",
)