import os

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash

from app.auth import require_role, verify_token
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse, UserRoleUpdate

load_dotenv()
router = APIRouter()

password_hash = PasswordHash.recommended()
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")


@router.post("/users/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user is not None:
        db.close()
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = password_hash.hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role="user",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
    }


@router.post("/users/login", response_model=TokenResponse)
def login_user(user: UserLogin):
    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user is None:
        db.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    password_correct = password_hash.verify(user.password, existing_user.password)
    if not password_correct:
        db.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = jwt.encode(
        {"user_id": existing_user.id, "role": existing_user.role},
        secret_key,
        algorithm="HS256",
    )

    db.close()
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/user/me", response_model=UserResponse)
def get_current_user(payload: dict = Depends(verify_token)):
    db = SessionLocal()
    current_user = db.query(User).filter(User.id == payload["user_id"]).first()
    db.close()

    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return current_user


@router.get("/user/admin-test")
def admin_test(payload: dict = Depends(require_role("admin"))):
    return {
        "message": "You are an admin",
        "user_id": payload["user_id"],
    }


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    payload: dict = Depends(require_role("admin")),
):
    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role_update.role.value
    db.commit()
    db.refresh(user)
    db.close()

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "role": user.role,
    }
