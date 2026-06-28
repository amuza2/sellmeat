import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    customer = "customer"
    seller = "seller"


class User(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str | None = None
    role: UserRole = UserRole.customer


class UserLogin(BaseModel):
    email: str
    password: str
