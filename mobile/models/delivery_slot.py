import uuid
from datetime import time

from pydantic import BaseModel


class DeliverySlot(BaseModel):
    id: uuid.UUID
    label: str
    delivery_time: time
    is_active: bool
