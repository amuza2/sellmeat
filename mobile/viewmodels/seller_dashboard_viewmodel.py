from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.order import Order
from services.api import APIClient


class SellerDashboardViewModel(ViewModelBase):
    orders = ObservableProperty([])
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_command = AsyncCommand(self._load)

    async def _load(self):
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
    def pending_count(self) -> int:
        return len([o for o in self.orders if o.status.value == "pending"])

    @property
    def preparation_count(self) -> int:
        return len([o for o in self.orders if o.status.value == "preparation"])

    @property
    def delivering_count(self) -> int:
        return len([o for o in self.orders if o.status.value == "delivering"])

    @property
    def delivered_count(self) -> int:
        return len([o for o in self.orders if o.status.value == "delivered"])

    @property
    def unpaid_count(self) -> int:
        return len([o for o in self.orders if o.payment_status.value == "unpaid"])

    @property
    def total_revenue(self) -> float:
        return sum(float(o.total_amount) for o in self.orders if o.status.value == "delivered")

    @property
    def recent_orders(self) -> list[Order]:
        return self.orders[:3]
