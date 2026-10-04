from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    message: str


class CommentResponse(BaseModel):
    id: int
    message: str
    user_id: int
    ticket_id: int
    created_at: datetime