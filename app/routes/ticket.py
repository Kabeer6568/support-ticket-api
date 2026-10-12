from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_role, verify_token
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketPageResponse,
    TicketResponse,
    TicketUpdate,
)

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


@router.post("/ticket", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate, payload: dict = Depends(verify_token)):
    db = SessionLocal()

    new_ticket = Ticket(
        title=ticket.title,
        desc=ticket.desc,
        user_id=payload["user_id"],
        status="pending",
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    db.close()

    return new_ticket


@router.get("/ticket", response_model=TicketPageResponse)
def get_my_tickets(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    payload: dict = Depends(verify_token),
):
    db = SessionLocal()
    query = db.query(Ticket)

    role = payload.get("role")
    if role == "user":
        query = query.filter(Ticket.user_id == payload["user_id"])
    elif role == "support_agent":
        query = query.filter(Ticket.assigned_to == payload["user_id"])
    elif role != "admin":
        db.close()
        raise HTTPException(status_code=403, detail="You do not have permission to access tickets")

    if status is not None:
        query = query.filter(Ticket.status == status)

    total = query.count()
    offset = (page - 1) * limit
    tickets = query.order_by(Ticket.id.asc()).offset(offset).limit(limit).all()
    db.close()

    return {
        "items": tickets,
        "page": page,
        "limit": limit,
        "total": total,
    }


@router.get("/ticket/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, payload: dict = Depends(verify_token)):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    db.close()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not can_access_ticket(payload, ticket):
        raise HTTPException(status_code=403, detail="You do not have access to this ticket")

    return ticket


@router.patch("/ticket/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
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

    if payload.get("role") == "user" and ticket.user_id != payload["user_id"]:
        db.close()
        raise HTTPException(status_code=403, detail="You can only update your own ticket")

    ticket.status = ticket_update.status.value
    db.commit()
    db.refresh(ticket)
    db.close()

    return ticket


@router.delete("/ticket/{ticket_id}")
def delete_ticket(ticket_id: int, payload: dict = Depends(require_role("admin"))):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(ticket)
    db.commit()
    db.close()

    return {
        "message": "Ticket deleted successfully",
        "ticket_id": ticket_id,
    }


@router.patch("/ticket/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    agent_id: int,
    payload: dict = Depends(require_role("admin")),
):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    agent = db.query(User).filter(User.id == agent_id).first()
    if agent is None:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    if agent.role != "support_agent":
        db.close()
        raise HTTPException(status_code=400, detail="User is not a support agent")

    ticket.assigned_to = agent.id
    db.commit()
    db.refresh(ticket)
    db.close()

    return {
        "message": "Ticket assigned successfully",
        "ticket_id": ticket.id,
        "assigned_to": ticket.assigned_to,
    }
