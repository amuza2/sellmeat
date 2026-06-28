import uuid
from datetime import date
from decimal import Decimal

from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.product import Product, UnitType
from models.order import DeliverySlot, OrderCreate, OrderItemCreate, Order
from models.settings import AppSettings
from services.api import APIClient


class CartItem:
    def __init__(self, product: Product, quantity: Decimal):
        self.product = product
        self.quantity = quantity

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.product.price

    @property
    def unit_label(self) -> str:
        return "kg" if self.product.unit_type == UnitType.weight else "unités"


class CartViewModel(ViewModelBase):
    items: list[CartItem] = []
    delivery_slots = ObservableProperty([])
    selected_slot = ObservableProperty(None)
    delivery_date = ObservableProperty(None)
    delivery_fee = ObservableProperty(Decimal("0"))
    notes = ObservableProperty("")
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    order_placed = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_slots_command = AsyncCommand(self._load_slots)
        self.place_order_command = AsyncCommand(self._place_order, self._can_place_order)

    def add_item(self, product: Product, quantity: Decimal):
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                self.notify("items")
                return
        self.items.append(CartItem(product, quantity))
        self.notify("items")

    def remove_item(self, index: int):
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.notify("items")

    def update_quantity(self, index: int, quantity: Decimal):
        if 0 <= index < len(self.items) and quantity > 0:
            self.items[index].quantity = quantity
            self.notify("items")

    @property
    def items_total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.items_total + self.delivery_fee

    @property
    def item_count(self) -> int:
        return len(self.items)

    def _can_place_order(self) -> bool:
        return len(self.items) > 0 and self.selected_slot is not None and self.delivery_date is not None

    async def _load_slots(self):
        self.is_loading = True
        self.notify("is_loading")
        try:
            self.delivery_slots = await self.api.list_delivery_slots(active_only=True)
            self.notify("delivery_slots")
            settings = await self.api.get_settings()
            self.delivery_fee = settings.delivery_fee
            self.notify("delivery_fee")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _place_order(self):
        self.is_loading = True
        self.error = ""
        self.notify("is_loading")
        try:
            order_data = OrderCreate(
                delivery_slot_id=self.selected_slot.id,
                delivery_date=self.delivery_date.date() if hasattr(self.delivery_date, 'date') else self.delivery_date,
                items=[
                    OrderItemCreate(product_id=item.product.id, quantity=item.quantity)
                    for item in self.items
                ],
                notes=self.notes if self.notes else None,
            )
            await self.api.create_order(order_data)
            self.items = []
            self.notes = ""
            self.order_placed = True
            self.notify("order_placed")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    def clear(self):
        self.items = []
        self.selected_slot = None
        self.delivery_date = None
        self.notes = ""
        self.order_placed = False
        self.error = ""
        self.notify("items")
