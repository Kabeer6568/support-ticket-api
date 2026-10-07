from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_token
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.comment import Comment
from app.ai.service import generate_ai_response


router = APIRouter()


@router.post("/ticket/{ticket_id}/ai-response")
def generate_ticket_ai_response(
    ticket_id: int,
    payload: dict = Depends(verify_token)
):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if ticket is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    user_id = payload["user_id"]
    role = payload["role"]

    # Customer can use AI on their own ticket
    if role == "user" and ticket.user_id != user_id:
        db.close()
        raise HTTPException(
            status_code=403,
            detail="You cannot access this ticket"
        )

    # Support agent can use AI on assigned ticket
    if (
        role == "support_agent"
        and ticket.assigned_to != user_id
    ):
        db.close()
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this ticket"
        )

    comments = db.query(Comment).filter(
        Comment.ticket_id == ticket_id
    ).order_by(
        Comment.created_at.asc()
    ).all()

    if not comments:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Ticket has no conversation yet"
        )

    conversation = ""

    for comment in comments:
        conversation += (
            f"User {comment.user_id}: "
            f"{comment.message}\n"
        )

    ai_response = generate_ai_response(conversation)

    db.close()

    return {
        "ticket_id": ticket.id,
        "response": ai_response
    }