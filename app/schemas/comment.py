from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    message: str
    user_id: int
    ticket_id: int
    created_at: datetime
