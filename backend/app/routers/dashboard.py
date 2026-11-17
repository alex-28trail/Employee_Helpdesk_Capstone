"""Dashboard summary (F4.4) and requester picker."""
from fastapi import APIRouter, Depends
from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AIFeedback, AISuggestion, Requester, Ticket
from app.schemas.enums import Category, Priority, Status
from app.schemas.ticket import AIStats, DashboardSummary, RequesterOut

router = APIRouter(prefix="/api", tags=["Dashboard"])


def _counts(db: Session, column, values) -> dict[str, int]:
    # Aggregate query (F2.4) - same as "counts_by_*" in database/queries.sql
    rows = db.execute(select(column, func.count(Ticket.id)).group_by(column)).all()
    found = {key: count for key, count in rows}
    return {v.value: found.get(v.value, 0) for v in values}


def _pct(part: int, whole: int) -> float | None:
    return round(100 * part / whole, 1) if whole else None


def _ai_stats(db: Session) -> AIStats:
    suggestions, tickets_analysed = db.execute(
        select(func.count(AISuggestion.id), func.count(distinct(AISuggestion.ticket_id)))
    ).one()
    reviewed, accepted, useful = db.execute(
        select(
            func.count(AIFeedback.id),
            func.coalesce(func.sum(case((AIFeedback.decision == "accepted", 1), else_=0)), 0),
            func.coalesce(func.sum(case((AIFeedback.useful.is_(True), 1), else_=0)), 0),
        )
    ).one()
    return AIStats(
        suggestions=suggestions,
        tickets_analysed=tickets_analysed,
        reviewed=reviewed,
        accepted=accepted,
        corrected=reviewed - accepted,
        useful=useful,
        acceptance_rate=_pct(accepted, reviewed),
        useful_rate=_pct(useful, reviewed),
    )


@router.get("/dashboard/summary", response_model=DashboardSummary,
            summary="Ticket counts by status, priority, category, plus AI feedback stats")
def dashboard_summary(db: Session = Depends(get_db)):
    by_status = _counts(db, Ticket.status, Status)
    return DashboardSummary(
        total=sum(by_status.values()),
        by_status=by_status,
        by_priority=_counts(db, Ticket.priority, Priority),
        by_category=_counts(db, Ticket.category, Category),
        ai=_ai_stats(db),
    )


@router.get("/requesters", response_model=list[RequesterOut], summary="Requesters for the employee picker")
def list_requesters(db: Session = Depends(get_db)):
    return db.scalars(select(Requester).order_by(Requester.name)).all()
