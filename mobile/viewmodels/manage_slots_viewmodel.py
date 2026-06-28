from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.order import DeliverySlot
from services.api import APIClient


class ManageSlotsViewModel(ViewModelBase):
    slots = ObservableProperty([])
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    new_label = ObservableProperty("")
    new_time = ObservableProperty("09:00")

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_command = AsyncCommand(self._load)
        self.create_command = AsyncCommand(self._create)
        self.delete_command = AsyncCommand(self._delete)
        self.toggle_active_command = AsyncCommand(self._toggle_active)

    async def _load(self):
        self.is_loading = True
        self.notify("is_loading")
        try:
            self.slots = await self.api.list_delivery_slots()
            self.notify("slots")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _create(self):
        if not self.new_label or not self.new_time:
            return
        try:
            await self.api.create_delivery_slot(self.new_label, self.new_time)
            self.new_label = ""
            self.notify("new_label")
            await self._load()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _delete(self, slot_id: str):
        try:
            await self.api.delete_delivery_slot(slot_id)
            await self._load()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _toggle_active(self, slot: DeliverySlot):
        try:
            await self.api.update_delivery_slot(str(slot.id), {"is_active": not slot.is_active})
            await self._load()
        except Exception as e:
            self.error = str(e)
            self.notify("error")
