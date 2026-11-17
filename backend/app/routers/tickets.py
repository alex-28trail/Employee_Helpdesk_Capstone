
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models import Ticket, Requester
from backend.app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse
)

router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"]
)


# 1. Create a new ticket
@router.post("/", response_model=TicketResponse, status_code=201)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):

    requester = db.query(Requester).filter(
        Requester.id == ticket.requester_id
    ).first()

    if not requester:
        raise HTTPException(
            status_code=404,
            detail="Requester not found"
        )

    new_ticket = Ticket(
        requester_id=ticket.requester_id,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


# 2. Get all tickets
@router.get("/", response_model=list[TicketResponse])
def get_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).all()


# 3. Get ticket by ID
@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket


# 4. Update ticket details
@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db)
):

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    update_data = ticket_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(ticket, key, value)

    db.commit()
    db.refresh(ticket)

    return ticket
