from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.order import Order, OrderStatus, PaymentStatus
from services.api import APIClient


class OrderDetailViewModel(ViewModelBase):
    order = ObservableProperty(None)
    customer_history = ObservableProperty([])
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_order_command = AsyncCommand(self._load_order)
        self.update_status_command = AsyncCommand(self._update_status)
        self.update_payment_command = AsyncCommand(self._update_payment)
        self.update_order_command = AsyncCommand(self._update_order)
        self.add_item_command = AsyncCommand(self._add_item)
        self.remove_item_command = AsyncCommand(self._remove_item)
        self.archive_order_command = AsyncCommand(self._archive_order)
        self.load_customer_history_command = AsyncCommand(self._load_customer_history)

    async def _load_order(self, order_id: str):
        self.is_loading = True
        self.notify("is_loading")
        try:
            self.order = await self.api.get_order(order_id)
            self.notify("order")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _update_status(self, status: OrderStatus):
        if not self.order:
            return
        try:
            self.order = await self.api.update_order_status(str(self.order.id), status)
            self.notify("order")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _update_payment(self, payment_status: PaymentStatus):
        if not self.order:
            return
        try:
            self.order = await self.api.update_order_payment(str(self.order.id), payment_status)
            self.notify("order")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _update_order(self, data: dict):
        if not self.order:
            return
        try:
            self.order = await self.api.update_order(str(self.order.id), data)
            self.notify("order")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _add_item(self, product_id: str, quantity: float):
        if not self.order:
            return
        try:
            self.order = await self.api.add_order_item(str(self.order.id), product_id, quantity)
            self.notify("order")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _remove_item(self, item_id: str):
        if not self.order:
            return
        try:
            self.order = await self.api.remove_order_item(str(self.order.id), item_id)
            self.notify("order")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _archive_order(self, order_id: str, archived: bool = True):
        try:
            await self.api.archive_order(order_id, archived)
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _load_customer_history(self):
        if not self.order:
            return
        try:
            self.customer_history = await self.api.get_customer_orders(str(self.order.customer_id))
            self.notify("customer_history")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
