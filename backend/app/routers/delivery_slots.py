import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_seller
from app.models.delivery_slot import DeliverySlot
from app.models.user import User
from app.schemas.delivery_slot import DeliverySlotCreate, DeliverySlotUpdate, DeliverySlotOut

router = APIRouter(prefix="/delivery-slots", tags=["delivery-slots"])


@router.get("", response_model=list[DeliverySlotOut])
def list_delivery_slots(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(DeliverySlot)
    if active_only:
        query = query.filter(DeliverySlot.is_active == True)
    return query.order_by(DeliverySlot.delivery_time).all()


@router.post("", response_model=DeliverySlotOut, status_code=status.HTTP_201_CREATED)
def create_delivery_slot(payload: DeliverySlotCreate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    slot = DeliverySlot(label=payload.label, delivery_time=payload.delivery_time, is_active=payload.is_active)
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.put("/{slot_id}", response_model=DeliverySlotOut)
def update_delivery_slot(slot_id: uuid.UUID, payload: DeliverySlotUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    slot = db.query(DeliverySlot).filter(DeliverySlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery slot not found")
    if payload.label is not None:
        slot.label = payload.label
    if payload.delivery_time is not None:
        slot.delivery_time = payload.delivery_time
    if payload.is_active is not None:
        slot.is_active = payload.is_active
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_slot(slot_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    slot = db.query(DeliverySlot).filter(DeliverySlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery slot not found")
    db.delete(slot)
    db.commit()
