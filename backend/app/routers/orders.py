import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_seller
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, OrderPaymentUpdate, OrderUpdate, OrderItemAdd, OrderArchiveUpdate
from app.services.order import create_order as create_order_service

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        customer_id=order.customer_id,
        customer_name=order.customer.name if order.customer else "",
        customer_email=order.customer.email if order.customer else "",
        customer_phone=order.customer.phone if order.customer else None,
        delivery_slot_id=order.delivery_slot_id,
        delivery_slot_label=order.delivery_slot.label if order.delivery_slot else "",
        delivery_slot_time=order.delivery_slot.delivery_time.strftime("%H:%M") if order.delivery_slot else None,
        delivery_date=order.delivery_date,
        status=order.status,
        payment_status=order.payment_status,
        items_total=order.items_total,
        delivery_fee=order.delivery_fee,
        total_amount=order.total_amount,
        notes=order.notes,
        is_archived=order.is_archived,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "",
                "unit_type": item.unit_type,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ],
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = create_order_service(db, user.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return _order_to_out(order)


@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Order)
    if user.role == UserRole.customer:
        query = query.filter(Order.customer_id == user.id)
    orders = query.order_by(Order.created_at.desc()).all()
    return [_order_to_out(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if user.role == UserRole.customer and order.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order")
    return _order_to_out(order)


@router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: uuid.UUID, payload: OrderStatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.put("/{order_id}/payment", response_model=OrderOut)
def update_order_payment(order_id: uuid.UUID, payload: OrderPaymentUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.payment_status = payload.payment_status
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.get("/customer/{customer_id}", response_model=list[OrderOut])
def get_customer_orders(customer_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    orders = db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.created_at.desc()).all()
    return [_order_to_out(o) for o in orders]


@router.put("/{order_id}", response_model=OrderOut)
def update_order(order_id: uuid.UUID, payload: OrderUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if payload.delivery_slot_id is not None:
        order.delivery_slot_id = payload.delivery_slot_id
    if payload.delivery_date is not None:
        order.delivery_date = payload.delivery_date
    if payload.notes is not None:
        order.notes = payload.notes
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.post("/{order_id}/items", response_model=OrderOut)
def add_order_item(order_id: uuid.UUID, payload: OrderItemAdd, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    subtotal = payload.quantity * product.price
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        unit_type=product.unit_type,
        quantity=payload.quantity,
        unit_price=product.price,
        subtotal=subtotal,
    )
    db.add(order_item)
    order.items_total += subtotal
    order.total_amount = order.items_total + order.delivery_fee
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.delete("/{order_id}/items/{item_id}", response_model=OrderOut)
def remove_order_item(order_id: uuid.UUID, item_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    item = db.query(OrderItem).filter(OrderItem.id == item_id, OrderItem.order_id == order_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    order.items_total -= item.subtotal
    order.total_amount = order.items_total + order.delivery_fee
    db.delete(item)
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.put("/{order_id}/archive", response_model=OrderOut)
def archive_order(order_id: uuid.UUID, payload: OrderArchiveUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.is_archived = payload.is_archived
    db.commit()
    db.refresh(order)
    return _order_to_out(order)
