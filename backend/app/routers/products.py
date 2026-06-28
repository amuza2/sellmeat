import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_seller
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    category_id: uuid.UUID | None = Query(None),
    meat_type_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if meat_type_id:
        from app.models.category import Category
        query = query.join(Category).filter(Category.meat_type_id == meat_type_id)
    return query.order_by(Product.name).all()


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    product = Product(
        category_id=payload.category_id,
        name=payload.name,
        unit_type=payload.unit_type,
        price=payload.price,
        is_available=payload.is_available,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if payload.name is not None:
        product.name = payload.name
    if payload.unit_type is not None:
        product.unit_type = payload.unit_type
    if payload.price is not None:
        product.price = payload.price
    if payload.is_available is not None:
        product.is_available = payload.is_available
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(product)
    db.commit()
