"""Seed script — populates the database with sample data."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.meat_type import MeatType
from app.models.category import Category
from app.models.product import Product, UnitType
from app.models.delivery_slot import DeliverySlot
from app.models.settings import Settings
from app.services.auth import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Settings
    if not db.query(Settings).filter(Settings.id == 1).first():
        db.add(Settings(id=1, delivery_fee=Decimal("50.00")))

    # Seller
    if not db.query(User).filter(User.email == "seller@sellmeat.com").first():
        db.add(User(
            name="Seller Admin",
            email="seller@sellmeat.com",
            password_hash=hash_password("password123"),
            role=UserRole.seller,
        ))

    # Customer
    if not db.query(User).filter(User.email == "customer@example.com").first():
        db.add(User(
            name="John Customer",
            email="customer@example.com",
            phone="+213 555 000 000",
            password_hash=hash_password("password123"),
            role=UserRole.customer,
        ))

    # Meat types
    chicken = db.query(MeatType).filter(MeatType.name == "Chicken").first()
    if not chicken:
        chicken = MeatType(name="Chicken")
        db.add(chicken)
        db.flush()

    turkey = db.query(MeatType).filter(MeatType.name == "Turkey").first()
    if not turkey:
        turkey = MeatType(name="Turkey")
        db.add(turkey)
        db.flush()

    # Categories
    escalope = db.query(Category).filter(Category.meat_type_id == chicken.id, Category.name == "Escalope").first()
    if not escalope:
        escalope = Category(meat_type_id=chicken.id, name="Escalope")
        db.add(escalope)
        db.flush()

    abats = db.query(Category).filter(Category.meat_type_id == chicken.id, Category.name == "Les Abats").first()
    if not abats:
        abats = Category(meat_type_id=chicken.id, name="Les Abats")
        db.add(abats)
        db.flush()

    turkey_escalope = db.query(Category).filter(Category.meat_type_id == turkey.id, Category.name == "Escalope").first()
    if not turkey_escalope:
        turkey_escalope = Category(meat_type_id=turkey.id, name="Escalope")
        db.add(turkey_escalope)
        db.flush()

    # Products
    if not db.query(Product).filter(Product.name == "Chicken Escalope Premium").first():
        db.add(Product(category_id=escalope.id, name="Chicken Escalope Premium", unit_type=UnitType.weight, price=Decimal("450.00")))
    if not db.query(Product).filter(Product.name == "Chicken Escalope Standard").first():
        db.add(Product(category_id=escalope.id, name="Chicken Escalope Standard", unit_type=UnitType.weight, price=Decimal("380.00")))
    if not db.query(Product).filter(Product.name == "Chicken Liver").first():
        db.add(Product(category_id=abats.id, name="Chicken Liver", unit_type=UnitType.weight, price=Decimal("250.00")))
    if not db.query(Product).filter(Product.name == "Chicken Hearts").first():
        db.add(Product(category_id=abats.id, name="Chicken Hearts", unit_type=UnitType.unit, price=Decimal("30.00")))
    if not db.query(Product).filter(Product.name == "Turkey Escalope Premium").first():
        db.add(Product(category_id=turkey_escalope.id, name="Turkey Escalope Premium", unit_type=UnitType.weight, price=Decimal("550.00")))

    # Delivery slots
    if not db.query(DeliverySlot).filter(DeliverySlot.label == "Morning").first():
        db.add(DeliverySlot(label="Morning", delivery_time="09:00"))
    if not db.query(DeliverySlot).filter(DeliverySlot.label == "Afternoon").first():
        db.add(DeliverySlot(label="Afternoon", delivery_time="13:00"))

    db.commit()
    db.close()
    print("Seed data inserted successfully!")


if __name__ == "__main__":
    seed()
