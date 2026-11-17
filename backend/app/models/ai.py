"""ORM models for ai_suggestions and ai_feedback.

Suggestions live in their own table, separate from the ticket's confirmed
category/priority, so an AI proposal can never silently overwrite human values.
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

_CATEGORIES = "('Hardware','Software','Network','Access','Other')"
_PRIORITIES = "('Low','Medium','High')"


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"
    __table_args__ = (
        CheckConstraint(f"suggested_category IN {_CATEGORIES}", name="ck_ai_suggestions_category"),
        CheckConstraint(f"suggested_priority IN {_PRIORITIES}", name="ck_ai_suggestions_priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    suggested_category: Mapped[str] = mapped_column(String(20))
    suggested_priority: Mapped[str] = mapped_column(String(10))
    priority_reason: Mapped[str] = mapped_column(Text)
    troubleshooting_steps: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(20))
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    feedback: Mapped["AIFeedback | None"] = relationship(back_populates="suggestion", uselist=False)


class AIFeedback(Base):
    __tablename__ = "ai_feedback"
    __table_args__ = (
        CheckConstraint("decision IN ('accepted','corrected')", name="ck_ai_feedback_decision"),
        CheckConstraint(f"final_category IN {_CATEGORIES}", name="ck_ai_feedback_category"),
        CheckConstraint(f"final_priority IN {_PRIORITIES}", name="ck_ai_feedback_priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suggestion_id: Mapped[int] = mapped_column(
        ForeignKey("ai_suggestions.id", ondelete="CASCADE"), unique=True  # one verdict per suggestion
    )
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    decision: Mapped[str] = mapped_column(String(10))
    useful: Mapped[bool] = mapped_column(Boolean)
    final_category: Mapped[str] = mapped_column(String(20))
    final_priority: Mapped[str] = mapped_column(String(10))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    suggestion: Mapped[AISuggestion] = relationship(back_populates="feedback")
