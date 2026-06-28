from decimal import Decimal

from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.order import Order, OrderStatus, PaymentStatus
from services.api import APIClient


class SellerOrdersViewModel(ViewModelBase):
    orders = ObservableProperty([])
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    status_filter = ObservableProperty(None)
    payment_filter = ObservableProperty(None)
    show_archived = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_orders_command = AsyncCommand(self._load_orders)
        self.update_status_command = AsyncCommand(self._update_status)
        self.update_payment_command = AsyncCommand(self._update_payment)
        self.archive_order_command = AsyncCommand(self._archive_order)

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

    async def _update_status(self, order_id: str, status: OrderStatus):
        try:
            await self.api.update_order_status(order_id, status)
            await self._load_orders()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _update_payment(self, order_id: str, payment_status: PaymentStatus):
        try:
            await self.api.update_order_payment(order_id, payment_status)
            await self._load_orders()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    @property
    def filtered_orders(self) -> list[Order]:
        result = self.orders
        if not self.show_archived:
            result = [o for o in result if not o.is_archived]
        if self.status_filter:
            result = [o for o in result if o.status == self.status_filter]
        if self.payment_filter:
            result = [o for o in result if o.payment_status == self.payment_filter]
        return result

    @property
    def pending_count(self) -> int:
        return len([o for o in self.orders if o.status == OrderStatus.pending and not o.is_archived])

    @property
    def unpaid_total(self) -> Decimal:
        return sum(
            (o.total_amount for o in self.orders if o.payment_status == PaymentStatus.unpaid and not o.is_archived),
            Decimal("0"),
        )

    def set_filters(self, status=None, payment=None):
        self.status_filter = status
        self.notify("status_filter")
        self.payment_filter = payment
        self.notify("payment_filter")

    async def _archive_order(self, order_id: str, archived: bool = True):
        try:
            await self.api.archive_order(order_id, archived)
            await self._load_orders()
        except Exception as e:
            self.error = str(e)
            self.notify("error")
