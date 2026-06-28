import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_seller
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(meat_type_id: uuid.UUID | None = Query(None), db: Session = Depends(get_db)):
    query = db.query(Category)
    if meat_type_id:
        query = query.filter(Category.meat_type_id == meat_type_id)
    return query.order_by(Category.name).all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    category = Category(meat_type_id=payload.meat_type_id, name=payload.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: uuid.UUID, payload: CategoryUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category.name = payload.name
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    db.delete(category)
    db.commit()
