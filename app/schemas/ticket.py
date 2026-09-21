from pydantic import BaseModel

class TicketCreate(BaseModel):
    title: str
    desc: str
