import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_seller
from app.models.meat_type import MeatType
from app.models.user import User
from app.schemas.meat_type import MeatTypeCreate, MeatTypeUpdate, MeatTypeOut

router = APIRouter(prefix="/meat-types", tags=["meat-types"])


@router.get("", response_model=list[MeatTypeOut])
def list_meat_types(db: Session = Depends(get_db)):
    return db.query(MeatType).order_by(MeatType.name).all()


@router.post("", response_model=MeatTypeOut, status_code=status.HTTP_201_CREATED)
def create_meat_type(payload: MeatTypeCreate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    meat_type = MeatType(name=payload.name)
    db.add(meat_type)
    db.commit()
    db.refresh(meat_type)
    return meat_type


@router.put("/{meat_type_id}", response_model=MeatTypeOut)
def update_meat_type(meat_type_id: uuid.UUID, payload: MeatTypeUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    meat_type = db.query(MeatType).filter(MeatType.id == meat_type_id).first()
    if not meat_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meat type not found")
    meat_type.name = payload.name
    db.commit()
    db.refresh(meat_type)
    return meat_type


@router.delete("/{meat_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meat_type(meat_type_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    meat_type = db.query(MeatType).filter(MeatType.id == meat_type_id).first()
    if not meat_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meat type not found")
    db.delete(meat_type)
    db.commit()
