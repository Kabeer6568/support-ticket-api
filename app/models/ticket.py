from sqlalchemy import Integer, String, Column, Text, ForeignKey
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    desc = Column(Text, nullable=False)
    status = Column(String(20), default="open")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
