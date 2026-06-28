from decimal import Decimal

from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from services.api import APIClient


class ManageSettingsViewModel(ViewModelBase):
    delivery_fee = ObservableProperty("")
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    is_saved = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_command = AsyncCommand(self._load)
        self.save_command = AsyncCommand(self._save)

    async def _load(self):
        self.is_loading = True
        self.notify("is_loading")
        try:
            settings = await self.api.get_settings()
            self.delivery_fee = str(settings.delivery_fee)
            self.notify("delivery_fee")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _save(self):
        if not self.delivery_fee:
            return
        try:
            await self.api.update_settings(float(self.delivery_fee))
            self.is_saved = True
            self.notify("is_saved")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
