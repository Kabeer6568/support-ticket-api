from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.database import SessionLocal
from app.auth import verify_token, require_role
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter()


@router.post("/ticket")
def create_ticket(
    ticket: TicketCreate,
    payload: dict = Depends(verify_token)
):
    db = SessionLocal()

    new_ticket = Ticket(
        title=ticket.title,
        desc=ticket.desc,
        user_id=payload["user_id"]
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    db.close()

    return {
        "message": "Ticket created successfully",
        "ticket_id": new_ticket.id,
        "user_id": new_ticket.user_id
    }


@router.get("/ticket")
def get_my_tickets(
    status: str | None = Query(default=None),
    page: int = Query(default=1 , ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    payload: dict = Depends(verify_token)
):
    db = SessionLocal()
    query = db.query(Ticket)

#Users can only there tickets
    if payload["role"] == "user":
        query = query.filter(
            Ticket.user_id == payload["user_id"]
        )
    elif payload["role"] == "support_agent":
        query = query.filter(
        Ticket.assigned_to == payload["user_id"]
    )
    
#filter by status
    if status is not None:
        query = query.filter(
            Ticket.status == status
        )

#Total number of matching tickets
    total = query.count()

#calculate records to skip
    offset = (page - 1)*limit

#Get only requested page
    tickets = query.offset(offset).limit(limit).all()

    db.close()

    return{
        "items": tickets,
        "page": page,
        "limit": limit,
        "total": total
    }


@router.get("/ticket/{ticket_id}")
def get_ticket(
    ticket_id: int,
    payload: dict = Depends(verify_token)
):
    db = SessionLocal()

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == payload["user_id"]
    ).first()

    db.close()

    if ticket is None:
        raise HTTPException (
            status_code=404,
            detail="Ticket Not Fund"
        )

    return ticket


@router.patch("/ticket/{ticket_id}")
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    payload: dict = Depends(verify_token)
):
    db = SessionLocal()

    if payload["role"] in ["admin", "support_agent"]:

        ticket = db.query(Ticket).filter(
            Ticket.id == ticket_id
        ).first()

    else:
        ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == payload["user_id"]
    ).first()

    if ticket is None:
        db.close()

        raise HTTPException (
            status_code=404,
            detail="Ticket Not Fund"
        )

    ticket.status = ticket_update.status.value

    db.commit()
    db.refresh(ticket)
    db.close()

    return {
        "message": "Ticket updated successfully",
        "ticket_id": ticket.id,
        "status": ticket.status
    }

@router.delete("/ticket/{ticket_id}")
def delete_ticket(
    ticket_id : int,
    payload: dict = Depends(require_role("admin"))
):

    db = SessionLocal()

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == payload['user_id']
    ).first()

    if ticket is None:

        db.close()

        raise HTTPException (
            status_code=404,
            detail="Ticket Not Fund"
        )

    db.delete(ticket)
    db.commit()
    db.close()

    return{
        "message": "Ticket deleted successfully",
        "ticket_id": ticket_id
    }


@router.patch("/ticket/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    agent_id: int,
    payload: dict = Depends(require_role("admin"))
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

    agent = db.query(User).filter(
        User.id == agent_id
    ).first()

    if agent is None:
        db.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if agent.role != "support_agent":
        db.close()

        raise HTTPException(
            status_code=400,
            detail="User is not a support agent"
        )

    ticket.assigned_to = agent.id

    db.commit()
    db.refresh(ticket)
    db.close()

    return {
        "message": "Ticket assigned successfully",
        "ticket_id": ticket.id,
        "assigned_to": ticket.assigned_to
    }