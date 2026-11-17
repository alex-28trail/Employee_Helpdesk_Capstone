"""Support workflow: status transitions and comments (F4.1-F4.3).

Status changes happen only here, and only through the allowed transitions.
Nothing in the AI code path calls this, so the AI can never close a ticket.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TicketActivity
from app.routers.tickets import get_ticket_or_404
from app.schemas.enums import Status
from app.schemas.ticket import ActivityOut, CommentCreate, StatusChange, TicketResponse

router = APIRouter(prefix="/api/tickets", tags=["Workflow"])
logger = logging.getLogger("helpdesk.workflow")

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Status.NEW.value: {Status.IN_PROGRESS.value},
    Status.IN_PROGRESS.value: {Status.RESOLVED.value},
    Status.RESOLVED.value: {Status.IN_PROGRESS.value},  # reopen
}


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Change status (New -> In Progress -> Resolved, reopen allowed)",
    responses={409: {"description": "Transition not allowed"}},
)
def change_status(ticket_id: int, payload: StatusChange, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(db, ticket_id)
    old, new = ticket.status, payload.status.value

    if new not in ALLOWED_TRANSITIONS.get(old, set()):
        allowed = ", ".join(sorted(ALLOWED_TRANSITIONS.get(old, set()))) or "none"
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot change status from '{old}' to '{new}'. Allowed next status: {allowed}.",
        )

    ticket.status = new
    verb = "reopened" if old == Status.RESOLVED.value else f"moved to {new}"
    description = f"Status {verb}" + (f". Note: {payload.note}" if payload.note else "")
    db.add(TicketActivity(
        ticket_id=ticket.id,
        performed_by=payload.performed_by,
        activity_type="status_change",
        description=description,
        old_status=old,
        new_status=new,
    ))
    db.commit()
    db.refresh(ticket)
    logger.info("event=ticket_status_changed ticket_id=%s old=%s new=%s", ticket.id, old, new)
    return ticket


@router.post(
    "/{ticket_id}/comments",
    response_model=ActivityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a support comment (visible in history)",
)
def add_comment(ticket_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(db, ticket_id)
    activity = TicketActivity(
        ticket_id=ticket.id,
        performed_by=payload.author,
        activity_type="comment",
        description=payload.comment,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    logger.info("event=ticket_comment_added ticket_id=%s activity_id=%s", ticket.id, activity.id)
    return activity
