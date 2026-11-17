from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db import Base


class TicketActivity(Base):
    """One row per event on a ticket: created, updated, status_change, comment, ai_analysis, ai_feedback."""

    __tablename__ = "ticket_activity"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    performed_by = Column(String(100), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    # Filled for status changes (and ticket creation), so history shows old -> new.
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
