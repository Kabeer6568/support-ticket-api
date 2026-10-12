import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func

from app.ai.service import AIServiceError, TicketTriage, triage_ticket
from app.auth import require_role, verify_token
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.ticket_triage import TicketTriageResult
from app.models.user import User
from app.schemas.ai import TicketTriageResponse
from app.schemas.ticket import (
    TicketCreate,
    TicketCreateResponse,
    TicketPageResponse,
    TicketResponse,
    TicketUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.post(
    "/ticket",
    response_model=TicketCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    ticket_id = new_ticket.id
    db.close()

    try:
        triage = triage_ticket(ticket.title, ticket.desc)
    except AIServiceError as exc:
        logger.warning("AI triage unavailable for ticket %s: %s", ticket_id, exc)
        triage = TicketTriage(
            decision="escalate",
            response=(
                "I couldn't safely resolve this automatically, so I'm sending "
                "your ticket to the support team."
            ),
            reason="AI triage was unavailable; a human review is required.",
            confidence=0.0,
        )

    db = SessionLocal()
    created_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if created_ticket is None:
        db.close()
        raise HTTPException(status_code=500, detail="Created ticket could not be loaded")

    assigned_agent = None
    outcome = "resolved"
    if triage.decision == "resolve":
        created_ticket.status = "resolved"
    else:
        outcome = "escalated"
        assigned_agent = (
            db.query(User)
            .filter(User.role == "support_agent")
            .order_by(func.random())
            .first()
        )
        created_ticket.status = "open"
        if assigned_agent is not None:
            created_ticket.assigned_to = assigned_agent.id
        else:
            triage = TicketTriage(
                decision="escalate",
                response=(
                    "I couldn't safely resolve this automatically. No support "
                    "agents are currently available, so an administrator will "
                    "need to assign your ticket."
                ),
                reason="No support agents are registered; admin assignment is required.",
                confidence=triage.confidence,
            )

    triage_record = TicketTriageResult(
        ticket_id=ticket_id,
        outcome=outcome,
        response=triage.response,
        reason=triage.reason,
        confidence=triage.confidence,
    )
    db.add(triage_record)
    db.commit()
    db.refresh(created_ticket)
    response = {
        "id": created_ticket.id,
        "title": created_ticket.title,
        "desc": created_ticket.desc,
        "status": created_ticket.status,
        "user_id": created_ticket.user_id,
        "assigned_to": created_ticket.assigned_to,
        "ai_outcome": outcome,
        "ai_response": triage.response,
        "ai_reason": triage.reason,
        "ai_confidence": triage.confidence,
    }
    db.close()
    return response


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


@router.get(
    "/ticket/{ticket_id}/triage",
    response_model=TicketTriageResponse | None,
)
def get_ticket_triage(ticket_id: int, payload: dict = Depends(verify_token)):
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not can_access_ticket(payload, ticket):
        db.close()
        raise HTTPException(status_code=403, detail="You do not have access to this ticket")

    triage = (
        db.query(TicketTriageResult)
        .filter(TicketTriageResult.ticket_id == ticket_id)
        .first()
    )
    if triage is None:
        db.close()
        return None

    result = {
        "outcome": triage.outcome,
        "response": triage.response,
        "reason": triage.reason,
        "confidence": triage.confidence,
        "assigned_to": ticket.assigned_to,
        "created_at": triage.created_at,
    }
    db.close()
    return result


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
