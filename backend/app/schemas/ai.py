"""Pydantic schemas for the AI feature (F5.3, F6)."""
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import Category, Priority

MAX_STEPS = 6
MAX_STEP_LENGTH = 200
MAX_REASON_LENGTH = 300
_LIST_PREFIX = re.compile(r"^\s*(\d+[.)]|[-*\u2022])\s*")


class AIAnalysisResult(BaseModel):
    """The exact shape the model must return. Anything that fails here is never saved."""

    model_config = ConfigDict(extra="ignore")

    category: Category
    priority: Priority
    priority_reason: str = Field(min_length=3, max_length=MAX_REASON_LENGTH)
    troubleshooting_steps: list[str] = Field(min_length=1, max_length=MAX_STEPS)

    @field_validator("category", "priority", mode="before")
    @classmethod
    def normalise_case(cls, value):
        # Small models sometimes answer "high" or "network"; forgive case only, nothing else.
        return value.strip().capitalize() if isinstance(value, str) else value

    @field_validator("priority_reason", mode="before")
    @classmethod
    def strip_reason(cls, value):
        # Wordy models often overshoot; trim at a word boundary instead of rejecting the whole answer.
        if not isinstance(value, str):
            return value
        value = value.strip()
        if len(value) > MAX_REASON_LENGTH:
            value = value[: MAX_REASON_LENGTH - 3].rsplit(" ", 1)[0].rstrip(" ,;:") + "..."
        return value

    @field_validator("troubleshooting_steps", mode="before")
    @classmethod
    def clean_steps(cls, value):
        if not isinstance(value, list):
            return value  # let Pydantic reject it
        cleaned = []
        for step in value:
            if not isinstance(step, str):
                continue
            step = _LIST_PREFIX.sub("", step).strip()  # drop "1." / "-" prefixes
            if step:
                cleaned.append(step[:MAX_STEP_LENGTH])
        return cleaned[:MAX_STEPS]


class AIFeedbackIn(BaseModel):
    """Support staff's verdict on one suggestion."""

    decision: Literal["accepted", "corrected"]
    useful: bool
    final_category: Category | None = None
    final_priority: Priority | None = None
    comment: str | None = Field(default=None, max_length=1000)
    reviewed_by: str = Field(default="Support Staff", min_length=1, max_length=100)

    @model_validator(mode="after")
    def corrected_needs_final_values(self):
        if self.decision == "corrected" and (self.final_category is None or self.final_priority is None):
            raise ValueError("final_category and final_priority are required when decision is 'corrected'")
        return self


class AIFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suggestion_id: int
    ticket_id: int
    decision: str
    useful: bool
    final_category: Category
    final_priority: Priority
    comment: str | None
    created_at: datetime


class AISuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    ticket_id: int
    suggested_category: Category
    suggested_priority: Priority
    priority_reason: str
    troubleshooting_steps: list[str]
    model_name: str
    prompt_version: str
    latency_ms: int | None
    analyzed_at: datetime
    feedback: AIFeedbackOut | None = None
