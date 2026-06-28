import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class UnitType(str, Enum):
    weight = "weight"
    unit = "unit"


class MeatType(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime


class Category(BaseModel):
    id: uuid.UUID
    meat_type_id: uuid.UUID
    name: str
    created_at: datetime


class Product(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    unit_type: UnitType
    price: Decimal
    is_available: bool
    created_at: datetime


class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str
    unit_type: UnitType = UnitType.weight
    price: Decimal
    is_available: bool = True
