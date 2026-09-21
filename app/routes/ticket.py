from fastapi import APIRouter, Depends
from app.schemas.ticket import TicketCreate
from app.models import ticket
from app.database import SessionLocal
from app.auth import verify_token
from app.models.ticket import Ticket


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
        user_id=payload['user_id']
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    db.close

    return{
        "message": "Ticket created successfully",
        "ticket_id": new_ticket.id,
        "user_id": new_ticket.user_id
    }

@router.get("/ticket")
def get_my_tickets(
    payload : dict = Depends(verify_token)
):

    db = SessionLocal()

    tickets = db.query(Ticket).filter(
        Ticket.user_id == payload["user_id"]
    ).all()

    db.close()

    return tickets