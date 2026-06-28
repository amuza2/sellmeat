from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.order import Order, OrderStatus, PaymentStatus
from services.api import APIClient


class CustomerOrdersViewModel(ViewModelBase):
    orders = ObservableProperty([])
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_orders_command = AsyncCommand(self._load_orders)

    async def _load_orders(self):
        self.is_loading = True
        self.notify("is_loading")
        try:
            self.orders = await self.api.list_orders()
            self.notify("orders")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    @property
    def pending_orders(self) -> list[Order]:
        return [o for o in self.orders if o.status == OrderStatus.pending]

    @property
    def active_orders(self) -> list[Order]:
        active = {OrderStatus.pending, OrderStatus.preparation, OrderStatus.delivering}
        return [o for o in self.orders if o.status in active]

    @property
    def past_orders(self) -> list[Order]:
        past = {OrderStatus.delivered, OrderStatus.cancelled}
        return [o for o in self.orders if o.status in past]
