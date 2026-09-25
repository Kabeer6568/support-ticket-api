from pydantic import BaseModel
from enum import Enum

class TicketCreate(BaseModel):
    title: str
    desc: str

class TicketStatus(str, Enum):
    pending = "pending"
    on_hold = "on_hold"
    resolved = "resolved"
    discarded = "discarded"

class TicketUpdate(BaseModel):
    status: TicketStatus