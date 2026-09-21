import jwt
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


load_dotenv()

security = HTTPBearer()

secret_key = os.getenv("SECRET_KEY")


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
    token = credentials.credentials
    try:
        payload = jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"]
    )

        return payload

    except jwt.InvalidTokenError :
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )