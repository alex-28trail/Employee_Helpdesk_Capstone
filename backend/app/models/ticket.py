
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.db import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    requester_id = Column(
        Integer,
        ForeignKey("requesters.id"),
        nullable=False
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String(50), default="Other")
    priority = Column(String(20), default="Medium")
    status = Column(String(30), default="New")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
