"""Pydantic schemas for tickets, workflow, history and dashboard (F3, F4).

Category, priority and status use the shared enums, so any value outside the
contract is rejected with 422 before it reaches the database.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import Category, Priority, Status


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class RequesterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str
    name: str
    email: str
    department: Optional[str] = None


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requester_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=4000)
    category: Category = Category.OTHER
    priority: Priority = Priority.MEDIUM

    _strip_text = field_validator("title", "description", mode="before")(_strip)


class TicketUpdate(BaseModel):
    """Only these fields are editable. Status changes go through PATCH /status (extra fields -> 422)."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=4000)
    category: Optional[Category] = None
    priority: Optional[Priority] = None
    performed_by: str = Field("Support Staff", min_length=1, max_length=100)

    _strip_text = field_validator("title", "description", mode="before")(_strip)


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    title: str
    description: str
    category: Category
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    requester: Optional[RequesterOut] = None


class StatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Status
    performed_by: str = Field("Support Staff", min_length=1, max_length=100)
    note: Optional[str] = Field(None, max_length=1000)


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str = Field(..., min_length=1, max_length=2000)
    author: str = Field("Support Staff", min_length=1, max_length=100)

    _strip_text = field_validator("comment", "author", mode="before")(_strip)


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    activity_type: str
    performed_by: str
    description: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: datetime


class AIStats(BaseModel):
    """How the advisory AI is performing, based on staff feedback (human oversight loop)."""

    suggestions: int          # total AI analyses stored
    tickets_analysed: int     # distinct tickets with at least one suggestion
    reviewed: int             # suggestions that staff accepted or corrected
    accepted: int
    corrected: int
    useful: int               # reviews marked "useful"
    acceptance_rate: Optional[float] = None  # accepted / reviewed, 0-100
    useful_rate: Optional[float] = None      # useful / reviewed, 0-100


class DashboardSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_category: dict[str, int]
    ai: AIStats
