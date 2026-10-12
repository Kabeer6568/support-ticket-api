from fastapi import APIRouter, Depends, HTTPException

from app.ai.service import AIServiceError, generate_ai_response
from app.auth import verify_token
from app.database import SessionLocal
from app.models.comment import Comment
from app.models.ticket import Ticket

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


@router.post("/ticket/{ticket_id}/ai-response")
def generate_ticket_ai_response(ticket_id: int, payload: dict = Depends(verify_token)):
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
    if not comments:
        db.close()
        raise HTTPException(status_code=400, detail="Ticket has no conversation yet")

    conversation = ""
    for comment in comments:
        conversation += f"User {comment.user_id}: {comment.message}\n"

    db.close()

    try:
        ai_response = generate_ai_response(conversation)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="AI service is temporarily unavailable. Please try again later.",
        ) from exc

    return {
        "ticket_id": ticket.id,
        "response": ai_response,
    }
