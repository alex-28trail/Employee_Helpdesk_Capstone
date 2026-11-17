
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.app.db import Base


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(Integer, primary_key=True, index=True)

    suggestion_id = Column(
        Integer,
        ForeignKey("ai_suggestions.id"),
        nullable=False
    )

    reviewed_by = Column(String(100), nullable=False)
    feedback = Column(String(30), nullable=False)
    comments = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
