import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.product import UnitType


class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str
    unit_type: UnitType = UnitType.weight
    price: Decimal
    is_available: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    unit_type: UnitType | None = None
    price: Decimal | None = None
    is_available: bool | None = None


class ProductOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    name: str
    unit_type: UnitType
    price: Decimal
    is_available: bool
    created_at: datetime

    model_config = {"from_attributes": True}
