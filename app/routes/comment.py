from fastapi import APIRouter, Depends, HTTPException

from app.ai.service import generate_ai_response
from app.auth import verify_token
from app.database import SessionLocal
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.schemas.comment import CommentCreate, CommentResponse

router = APIRouter()


def can_access_ticket(payload: dict, ticket: Ticket) -> bool:
    role = payload.get("role")
    user_id = payload.get("user_id")

    if role == "admin":
        return True
    if role == "user":
        return ticket.user_id == user_id
    if role == "support_agent":
        return ticket.assigned_to == user_id
    return False


@router.post("/ticket/{ticket_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    ticket_id: int,
    comment: CommentCreate,
    payload: dict = Depends(verify_token),
):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not can_access_ticket(payload, ticket):
        db.close()
        raise HTTPException(status_code=403, detail="You do not have access to this ticket")

    new_comment = Comment(
        message=comment.message,
        user_id=payload["user_id"],
        ticket_id=ticket.id,
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    db.close()

    return new_comment


@router.get("/ticket/{ticket_id}/comments", response_model=list[CommentResponse])
def get_ticket_comments(ticket_id: int, payload: dict = Depends(verify_token)):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not can_access_ticket(payload, ticket):
        db.close()
        raise HTTPException(status_code=403, detail="You do not have access to this ticket")

    comments = (
        db.query(Comment)
        .filter(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    db.close()

    return comments
