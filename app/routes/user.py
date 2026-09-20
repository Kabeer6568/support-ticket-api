from fastapi import APIRouter
from app.schemas.user import UserCreate, UserLogin
from app.database import SessionLocal
from app.models.user import User
from pwdlib import PasswordHash
import jwt

router = APIRouter()

password_hash = PasswordHash.recommended()
secret_key = "my-super-secret-key"


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
            "message" : "Invalid email "
        }

    password_correct = password_hash.verify(user.password, existing_user.password)

    if not password_correct:
        return{
            "message" : "Invalid password"
        }

    token = jwt.encode(
        {"user_id" : existing_user.id},
        secret_key,
        algorithm="HS256"
    )

    # return {
    #     "message": "User Found",
    #     "user_id": existing_user.id
    # }

    return {
        "message": "Password is correct",
        "user_id": existing_user.id,
        "access_token": token,
        "token_type": "bearer"
    }