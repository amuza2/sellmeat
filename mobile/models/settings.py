from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AppSettings(BaseModel):
    delivery_fee: Decimal
    updated_at: datetime
