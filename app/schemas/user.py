from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str

    @field_validator("role", mode="before")
    @classmethod
    def default_missing_role_to_customer(cls, value: str | None) -> str:
        return "user" if value is None else value


class UserPageResponse(BaseModel):
    items: list[UserResponse]
    page: int
    limit: int
    total: int


class UserRole(str, Enum):
    user = "user"
    support_agent = "support_agent"
    admin = "admin"


class UserRoleUpdate(BaseModel):
    role: UserRole
