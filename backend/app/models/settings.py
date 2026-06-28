from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
