
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.db import Base


class TicketActivity(Base):
    __tablename__ = "ticket_activity"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False
    )

    performed_by = Column(String(100), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
