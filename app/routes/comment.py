from fastapi import APIRouter, Depends, HTTPException, status

from app.database import SessionLocal
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.schemas.comment import CommentCreate, CommentResponse
from app.auth import verify_token


router = APIRouter()


@router.post(
    "/ticket/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    ticket_id: int,
    comment: CommentCreate,
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

    # Customer can comment only on their own ticket
    if role == "user" and ticket.user_id != user_id:
        db.close()
        raise HTTPException(
            status_code=403,
            detail="You cannot comment on this ticket"
        )

    # Support agent can comment only if assigned
    if (
        role == "support_agent"
        and ticket.assigned_to != user_id
    ):
        db.close()
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this ticket"
        )

    # Admin can comment on any ticket

    new_comment = Comment(
        message=comment.message,
        user_id=user_id,
        ticket_id=ticket.id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    db.close()

    return new_comment


@router.get(
    "/ticket/{ticket_id}/comments",
    response_model=list[CommentResponse]
)
def get_ticket_comments(
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

    # Customer can view only their own ticket
    if role == "user" and ticket.user_id != user_id:
        db.close()
        raise HTTPException(
            status_code=403,
            detail="You cannot view this ticket"
        )

    # Support agent can view only assigned ticket
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

    db.close()

    return comments