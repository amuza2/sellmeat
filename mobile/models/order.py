import uuid
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from models.product import UnitType


class OrderStatus(str, Enum):
    pending = "pending"
    preparation = "preparation"
    delivering = "delivering"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentStatus(str, Enum):
    unpaid = "unpaid"
    paid = "paid"


class DeliverySlot(BaseModel):
    id: uuid.UUID
    label: str
    delivery_time: time
    is_active: bool
    created_at: datetime


class OrderItem(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_type: UnitType
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal


class Order(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str
    customer_email: str = ""
    customer_phone: str | None = None
    delivery_slot_id: uuid.UUID
    delivery_slot_label: str
    delivery_slot_time: str | None = None
    delivery_date: date
    status: OrderStatus
    payment_status: PaymentStatus
    items_total: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    notes: str | None = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    items: list[OrderItem] = []


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal


class OrderCreate(BaseModel):
    delivery_slot_id: uuid.UUID
    delivery_date: date
    items: list[OrderItemCreate]
    notes: str | None = None
