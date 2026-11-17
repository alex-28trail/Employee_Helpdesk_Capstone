"""AI analysis and feedback endpoints (F6.1-F6.3).

Human-control guarantees enforced here:
- Running an analysis stores a suggestion only. Ticket category, priority and status are untouched.
- Ticket values change only when a staff member submits feedback, and only category/priority.
- Status is never modified by anything in this router.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.ai import AIFeedback, AISuggestion
from app.models.ticket import Ticket, TicketActivity
from app.schemas.ai import AIFeedbackIn, AIFeedbackOut, AISuggestionOut
from app.services.ai_service import AIService, AIServiceError, get_ai_service

router = APIRouter(prefix="/api", tags=["AI"])
logger = logging.getLogger("helpdesk.ai")

_DETAIL = {"content": {"application/json": {"example": {"detail": "Human-readable message"}}}}


def _ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ticket {ticket_id} not found")
    return ticket


@router.post(
    "/tickets/{ticket_id}/ai-analysis",
    response_model=AISuggestionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Run AI triage for a ticket and store the suggestion",
    responses={
        404: {"description": "Ticket not found", **_DETAIL},
        502: {"description": "Model returned invalid output", **_DETAIL},
        503: {"description": "Model unavailable", **_DETAIL},
        504: {"description": "Model timed out", **_DETAIL},
    },
)
def run_ai_analysis(ticket_id: int, db: Session = Depends(get_db), ai: AIService = Depends(get_ai_service)):
    ticket = _ticket_or_404(db, ticket_id)
    logger.info("event=ai_analysis_requested ticket_id=%s", ticket_id)

    try:
        outcome = ai.analyze_ticket(ticket.title, ticket.description)
    except AIServiceError as exc:
        # Nothing has been written yet, so the ticket is exactly as it was.
        logger.warning(
            "event=ai_analysis_failed ticket_id=%s error=%s http_status=%s",
            ticket_id, type(exc).__name__, exc.status_code,
        )
        raise HTTPException(exc.status_code, exc.message) from exc

    result = outcome.result
    suggestion = AISuggestion(
        ticket_id=ticket.id,
        suggested_category=result.category.value,
        suggested_priority=result.priority.value,
        priority_reason=result.priority_reason,
        troubleshooting_steps=result.troubleshooting_steps,
        model_name=outcome.model_name,
        prompt_version=outcome.prompt_version,
        latency_ms=outcome.latency_ms,
    )
    db.add(suggestion)
    db.add(TicketActivity(
        ticket_id=ticket.id,
        action="ai_analysis",
        note=f"AI suggested {result.category.value} / {result.priority.value} (advisory, not applied)",
    ))
    db.commit()
    db.refresh(suggestion)

    logger.info(
        "event=ai_analysis_succeeded ticket_id=%s suggestion_id=%s model=%s latency_ms=%s category=%s priority=%s",
        ticket_id, suggestion.id, outcome.model_name, outcome.latency_ms, result.category.value, result.priority.value,
    )
    return suggestion


@router.get(
    "/tickets/{ticket_id}/ai-suggestions",
    response_model=list[AISuggestionOut],
    summary="Latest AI suggestions for a ticket, newest first, with any feedback",
    responses={404: {"description": "Ticket not found", **_DETAIL}},
)
def list_ai_suggestions(
    ticket_id: int,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    _ticket_or_404(db, ticket_id)
    stmt = (
        select(AISuggestion)
        .where(AISuggestion.ticket_id == ticket_id)
        .options(selectinload(AISuggestion.feedback))
        .order_by(AISuggestion.analyzed_at.desc(), AISuggestion.id.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()


@router.post(
    "/ai-suggestions/{suggestion_id}/feedback",
    response_model=AIFeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Accept or correct a suggestion; applies the final values to the ticket",
    responses={
        404: {"description": "Suggestion not found", **_DETAIL},
        409: {"description": "Feedback already recorded for this suggestion", **_DETAIL},
        422: {"description": "Invalid feedback", **_DETAIL},
    },
)
def record_ai_feedback(suggestion_id: int, payload: AIFeedbackIn, db: Session = Depends(get_db)):
    suggestion = db.get(AISuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"AI suggestion {suggestion_id} not found")
    if suggestion.feedback is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Feedback has already been recorded for this suggestion. Run a new analysis to give feedback again.",
        )

    if payload.decision == "accepted":
        final_category, final_priority = suggestion.suggested_category, suggestion.suggested_priority
        if (payload.final_category and payload.final_category.value != final_category) or (
            payload.final_priority and payload.final_priority.value != final_priority
        ):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Accepted feedback must keep the suggested values. Use decision 'corrected' to change them.",
            )
    else:
        final_category, final_priority = payload.final_category.value, payload.final_priority.value
        if (final_category, final_priority) == (suggestion.suggested_category, suggestion.suggested_priority):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Corrected feedback must change the category or priority. Use decision 'accepted' if the suggestion was right.",
            )

    ticket = db.get(Ticket, suggestion.ticket_id)
    changes = []
    if ticket.category != final_category:
        changes.append(f"category {ticket.category or 'unset'} -> {final_category}")
    if ticket.priority != final_priority:
        changes.append(f"priority {ticket.priority or 'unset'} -> {final_priority}")

    # The human-confirmed values are applied here, and only here. Status is not touched.
    ticket.category = final_category
    ticket.priority = final_priority

    feedback = AIFeedback(
        suggestion_id=suggestion.id,
        ticket_id=ticket.id,
        decision=payload.decision,
        useful=payload.useful,
        final_category=final_category,
        final_priority=final_priority,
        comment=payload.comment,
    )
    db.add(feedback)
    db.add(TicketActivity(
        ticket_id=ticket.id,
        action="ai_feedback",
        note=(
            f"AI suggestion {payload.decision} by support"
            + (f": {', '.join(changes)}" if changes else "; ticket values unchanged")
            + f". Marked {'useful' if payload.useful else 'not useful'}."
        ),
    ))
    try:
        db.commit()
    except IntegrityError:  # two staff submitting at the same moment
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Feedback has already been recorded for this suggestion.")
    db.refresh(feedback)

    logger.info(
        "event=ai_feedback_recorded ticket_id=%s suggestion_id=%s decision=%s useful=%s final_category=%s final_priority=%s",
        ticket.id, suggestion.id, payload.decision, payload.useful, final_category, final_priority,
    )
    return feedback
