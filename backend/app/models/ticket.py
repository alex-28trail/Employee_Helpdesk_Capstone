from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base

CATEGORIES = "('Hardware','Software','Network','Access','Other')"
PRIORITIES = "('Low','Medium','High')"
STATUSES = "('New','In Progress','Resolved')"


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(f"category IN {CATEGORIES}", name="ck_tickets_category"),
        CheckConstraint(f"priority IN {PRIORITIES}", name="ck_tickets_priority"),
        CheckConstraint(f"status IN {STATUSES}", name="ck_tickets_status"),
    )

    id = Column(Integer, primary_key=True, index=True)

    requester_id = Column(
        Integer,
        ForeignKey("requesters.id"),
        nullable=False,
        index=True,
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String(50), nullable=False, default="Other")
    priority = Column(String(20), nullable=False, default="Medium")
    status = Column(String(30), nullable=False, default="New")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    requester = relationship("Requester", lazy="joined")
