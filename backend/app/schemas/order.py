import uuid
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel

from app.models.order import OrderStatus, PaymentStatus
from app.models.product import UnitType


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal


class OrderCreate(BaseModel):
    delivery_slot_id: uuid.UUID
    delivery_date: date
    items: list[OrderItemCreate]
    notes: str | None = None


class OrderItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_type: UnitType
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
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
    notes: str | None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderPaymentUpdate(BaseModel):
    payment_status: PaymentStatus


class OrderUpdate(BaseModel):
    delivery_slot_id: uuid.UUID | None = None
    delivery_date: date | None = None
    notes: str | None = None


class OrderItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal


class OrderArchiveUpdate(BaseModel):
    is_archived: bool
