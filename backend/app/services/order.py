from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product
from app.models.settings import Settings
from app.schemas.order import OrderCreate


def create_order(db: Session, customer_id, order_data: OrderCreate) -> Order:
    settings_row = db.query(Settings).filter(Settings.id == 1).first()
    delivery_fee = settings_row.delivery_fee if settings_row else Decimal("0.00")

    items_total = Decimal("0.00")
    order = Order(
        customer_id=customer_id,
        delivery_slot_id=order_data.delivery_slot_id,
        delivery_date=order_data.delivery_date,
        status=OrderStatus.pending,
        payment_status=PaymentStatus.unpaid,
        items_total=Decimal("0.00"),
        delivery_fee=delivery_fee,
        total_amount=Decimal("0.00"),
        notes=order_data.notes,
    )
    db.add(order)
    db.flush()

    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise ValueError(f"Product {item.product_id} not found")
        if not product.is_available:
            raise ValueError(f"Product {product.name} is not available")

        subtotal = item.quantity * product.price
        items_total += subtotal

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            unit_type=product.unit_type,
            quantity=item.quantity,
            unit_price=product.price,
            subtotal=subtotal,
        )
        db.add(order_item)

    order.items_total = items_total
    order.total_amount = items_total + delivery_fee

    db.commit()
    db.refresh(order)
    return order
