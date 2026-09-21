from fastapi import FastAPI
from app.database import engine, Base
from app.models.user import User
from app.models.ticket import Ticket
# from app.routes import ticket

Base.metadata.create_all(bind=engine)
from app.routes import user
from app.routes import ticket

app = FastAPI(
    title="Support Ticket API",
    description="Backend API for managing customer support tickets",
    version="1.0.0"
)
app.include_router(user.router)
app.include_router(ticket.router)

@app.get("/")
def home():
    return {
        "message": "Support Ticket API is running"
    }


@app.get("/db-test")
def db_test():
    try:
        with engine.connect():
            return {
                "message": "Database connection successful"
            }
    except Exception as e:
        return {
            "message": "Database connection failed",
            "error": str(e)
        }