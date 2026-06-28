from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SettingsOut(BaseModel):
    delivery_fee: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    delivery_fee: Decimal
