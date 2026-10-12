from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TicketTriageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    outcome: Literal["resolved", "escalated"]
    response: str
    reason: str
    confidence: float
    assigned_to: int | None
    created_at: datetime
