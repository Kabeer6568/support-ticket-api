from fastapi import APIRouter
from app.schemas.user import UserCreate, UserLogin
from app.database import SessionLocal
from app.models.user import User
from pwdlib import PasswordHash

router = APIRouter()

password_hash = PasswordHash.recommended()


@router.post("/users/register")
def register_user(user: UserCreate):
    db = SessionLocal()

    hashed_password = password_hash.hash(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@router.post("/users/login")
def login_user(user: UserLogin):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == user.email).first()
    
    db.close()

    if existing_user is None:
        return{
            "message" : "Invalid emal or password"
        }

    return {
        "message": "User Found",
        "user_id": existing_user.id
    }