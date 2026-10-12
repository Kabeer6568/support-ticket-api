from enum import Enum

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    desc: str = Field(..., min_length=1, max_length=5000)


class TicketStatus(str, Enum):
    pending = "pending"
    open = "open"
    on_hold = "on_hold"
    resolved = "resolved"
    discarded = "discarded"


class TicketUpdate(BaseModel):
    status: TicketStatus = TicketStatus.pending


class TicketResponse(BaseModel):
    id: int
    title: str
    desc: str
    status: str
    user_id: int
    assigned_to: int | None = None
