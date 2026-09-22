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

@router.get("/ticket/{ticket_id}")
def get_ticket(
    ticket_id: int,
    payload: dict = Depends(verify_token)
):

    db = SessionLocal()

    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == payload['user_id']
    ).first()

    db.close()

    if ticket is None:
        return{
            "message" : "Ticket Not Found"
        }

    return ticket