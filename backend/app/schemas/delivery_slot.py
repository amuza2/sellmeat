import uuid
from datetime import datetime, time

from pydantic import BaseModel


class DeliverySlotCreate(BaseModel):
    label: str
    delivery_time: time
    is_active: bool = True


class DeliverySlotUpdate(BaseModel):
    label: str | None = None
    delivery_time: time | None = None
    is_active: bool | None = None


class DeliverySlotOut(BaseModel):
    id: uuid.UUID
    label: str
    delivery_time: time
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
