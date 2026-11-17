"""Ticket CRUD and history (F3.1-F3.5)."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Requester, Ticket, TicketActivity
from app.schemas.enums import Category, Priority, Status
from app.schemas.ticket import ActivityOut, TicketCreate, TicketResponse, TicketUpdate

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])
logger = logging.getLogger("helpdesk.tickets")


def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ticket {ticket_id} not found")
    return ticket


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED, summary="Create a ticket")
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    requester = db.get(Requester, payload.requester_id)
    if requester is None:
        raise HTTPException(
            422,
            [{"loc": ["body", "requester_id"], "msg": f"Requester {payload.requester_id} does not exist",
              "type": "value_error"}],
        )

    ticket = Ticket(
        requester_id=payload.requester_id,
        title=payload.title,
        description=payload.description,
        category=payload.category.value,
        priority=payload.priority.value,
        status=Status.NEW.value,
    )
    db.add(ticket)
    db.flush()
    db.add(TicketActivity(
        ticket_id=ticket.id,
        performed_by=requester.name,
        activity_type="created",
        description="Ticket created",
        new_status=Status.NEW.value,
    ))
    db.commit()
    db.refresh(ticket)
    logger.info("event=ticket_created ticket_id=%s category=%s priority=%s", ticket.id, ticket.category, ticket.priority)
    return ticket


@router.get("", response_model=list[TicketResponse], summary="List tickets with requester (filterable)")
def list_tickets(
    status_: Optional[Status] = Query(None, alias="status"),
    category: Optional[Category] = None,
    priority: Optional[Priority] = None,
    requester_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    # Join query (F2.3) - same as "tickets_with_requester" in database/queries.sql
    stmt = select(Ticket).join(Ticket.requester).order_by(Ticket.created_at.desc(), Ticket.id.desc())
    if status_:
        stmt = stmt.where(Ticket.status == status_.value)
    if category:
        stmt = stmt.where(Ticket.category == category.value)
    if priority:
        stmt = stmt.where(Ticket.priority == priority.value)
    if requester_id:
        stmt = stmt.where(Ticket.requester_id == requester_id)
    return db.scalars(stmt).unique().all()


@router.get("/{ticket_id}", response_model=TicketResponse, summary="Ticket detail with requester")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return get_ticket_or_404(db, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketResponse, summary="Update title, description, category, priority")
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(db, ticket_id)
    data = payload.model_dump(exclude_unset=True, exclude={"performed_by"})

    changes = []
    for field, value in data.items():
        if value is None:
            continue
        value = value.value if hasattr(value, "value") else value
        old = getattr(ticket, field)
        if old != value:
            setattr(ticket, field, value)
            # Never write title/description text into history or logs - just note that they changed.
            changes.append(f"{field} {old} -> {value}" if field in ("category", "priority") else f"{field} edited")

    if changes:
        db.add(TicketActivity(
            ticket_id=ticket.id,
            performed_by=payload.performed_by,
            activity_type="updated",
            description="; ".join(changes),
        ))
        db.commit()
        db.refresh(ticket)
        logger.info("event=ticket_updated ticket_id=%s fields=%s", ticket.id, ",".join(sorted(data)))
    return ticket


@router.get("/{ticket_id}/history", response_model=list[ActivityOut], summary="Activity and status changes, oldest first")
def ticket_history(ticket_id: int, db: Session = Depends(get_db)):
    get_ticket_or_404(db, ticket_id)
    stmt = (
        select(TicketActivity)
        .where(TicketActivity.ticket_id == ticket_id)
        .order_by(TicketActivity.created_at.asc(), TicketActivity.id.asc())
    )
    return db.scalars(stmt).all()
