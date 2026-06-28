import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    role: UserRole = UserRole.customer

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone_for_customer(cls, v: str | None, info) -> str | None:
        role = info.data.get("role", UserRole.customer)
        if role == UserRole.customer and not v:
            raise ValueError("Phone number is required for customers")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
