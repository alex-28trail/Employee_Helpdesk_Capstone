"""FastAPI entry point.  Run from the backend/ folder:

    uvicorn app.main:app --reload
"""
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.logging_config import setup_logging
from app.routers import ai, dashboard, tickets, workflow
from app.services.ai_service import AIService, get_ai_service

setup_logging(settings.log_level)
logger = logging.getLogger("helpdesk")

app = FastAPI(
    title="AI Employee Helpdesk",
    description="Employee IT support tickets with advisory AI triage (local Ollama). "
                "The AI only suggests category, priority and steps; staff accept or correct them.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Any local dev port (Vite moves to 5174, 5175... when 5173 is busy).
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def home():
    return {"message": "AI Employee Helpdesk API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["Health"], summary="Database and AI model status, reported separately")
def health_check(db: Session = Depends(get_db), ai_service: AIService = Depends(get_ai_service)):
    try:
        db.execute(text("SELECT 1"))
        database = {"status": "ok"}
    except Exception:  # noqa: BLE001 - report, never crash the health check
        logger.warning("event=health_db_unavailable")
        database = {"status": "unavailable", "detail": "Database not reachable"}

    model = ai_service.health()
    overall = "ok" if database["status"] == "ok" and model["status"] == "ok" else "degraded"
    return {"status": overall, "database": database, "ai": model}


app.include_router(tickets.router)
app.include_router(workflow.router)
app.include_router(ai.router)
app.include_router(dashboard.router)
