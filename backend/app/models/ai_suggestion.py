
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.db import Base


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False
    )

    suggested_category = Column(String(50), nullable=False)
    suggested_priority = Column(String(20), nullable=False)
    priority_reason = Column(Text, nullable=True)
    troubleshooting_steps = Column(Text, nullable=True)

    model_name = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
