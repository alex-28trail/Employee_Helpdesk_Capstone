
from pydantic import BaseModel, Field
from typing import Optional


class TicketCreate(BaseModel):
    requester_id: int
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    category: Optional[str] = "Other"


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5)
    category: Optional[str] = None
    priority: Optional[str] = None


class TicketResponse(BaseModel):
    id: int
    requester_id: int
    title: str
    description: str
    category: str
    priority: str
    status: str

    model_config = {
        "from_attributes": True
    }
