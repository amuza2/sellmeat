import uuid
from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    meat_type_id: uuid.UUID
    name: str


class CategoryUpdate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: uuid.UUID
    meat_type_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
