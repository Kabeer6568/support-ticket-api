from pydantic import BaseModel, EmailStr
from enum import Enum



class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

class UserRole(str, Enum):
    user = "user"
    support_agent = "support_agent"
    admin = "admin"


class UserRoleUpdate(BaseModel):
    role: UserRole