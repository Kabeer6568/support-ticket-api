from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, UserRoleUpdate
from app.database import SessionLocal
from app.models.user import User
from pwdlib import PasswordHash
import jwt
import os
from dotenv import load_dotenv
from app.auth import verify_token, require_role

load_dotenv()
router = APIRouter()


password_hash = PasswordHash.recommended()
secret_key = os.getenv("SECRET_KEY")


@router.post("/users/register")
def register_user(user: UserCreate):
    db = SessionLocal()

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user is not None:
        db.close()

        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    hashed_password = password_hash.hash(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role="user"
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

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    db.close()

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_correct = password_hash.verify(
        user.password,
        existing_user.password
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = jwt.encode(
        {"user_id" : existing_user.id,"role": existing_user.role},
        secret_key,
        algorithm="HS256"
    )

    return {
        "message": "Password is correct",
        "user_id": existing_user.id,
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/user/me")
def get_current_user(user_id: int, payload: dict = Depends(verify_token)) :

    db = SessionLocal()

    current_user  = db.query(User).filter(
            User.id == user_id,
            User.id == payload["user_id"]
            ).first()

    db.close()

    if current_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return current_user 

@router.get('/user/admin-test')
def admin_test(
    payload: dict = Depends(require_role("admin"))
):
    return{
        "message": "You are an admin",
        "user_id": payload["user_id"]
    }


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    payload: dict = Depends(require_role("admin"))
):
    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.role = role_update.role.value

    db.commit()
    db.refresh(user)
    db.close()

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "role": user.role
    }