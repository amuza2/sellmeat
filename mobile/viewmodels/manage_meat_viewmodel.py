from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.product import MeatType, Category
from services.api import APIClient
import logging

logger = logging.getLogger(__name__)


class ManageMeatViewModel(ViewModelBase):
    meat_types = ObservableProperty([])
    categories = ObservableProperty([])
    selected_meat_type = ObservableProperty(None)
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    new_meat_type_name = ObservableProperty("")
    new_category_name = ObservableProperty("")

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_meat_types_command = AsyncCommand(self._load_meat_types)
        self.create_meat_type_command = AsyncCommand(self._create_meat_type)
        self.update_meat_type_command = AsyncCommand(self._update_meat_type)
        self.delete_meat_type_command = AsyncCommand(self._delete_meat_type)
        self.create_category_command = AsyncCommand(self._create_category)
        self.update_category_command = AsyncCommand(self._update_category)
        self.delete_category_command = AsyncCommand(self._delete_category)

    async def _load_meat_types(self):
        self.is_loading = True
        self.notify("is_loading")
        try:
            self.meat_types = await self.api.list_meat_types()
            self.notify("meat_types")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _create_meat_type(self):
        if not self.new_meat_type_name:
            return
        self.error = ""
        try:
            await self.api.create_meat_type(self.new_meat_type_name)
            self.new_meat_type_name = ""
            self.notify("new_meat_type_name")
            await self._load_meat_types()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _update_meat_type(self, meat_type_id: str, name: str):
        self.error = ""
        try:
            await self.api.update_meat_type(meat_type_id, name)
            await self._load_meat_types()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _delete_meat_type(self, meat_type_id: str):
        self.error = ""
        logger.info(f"Deleting meat type: {meat_type_id}")
        try:
            await self.api.delete_meat_type(meat_type_id)
            logger.info(f"Meat type deleted: {meat_type_id}")
            if self.selected_meat_type and str(self.selected_meat_type.id) == meat_type_id:
                self.selected_meat_type = None
                self.categories = []
                self.notify("selected_meat_type")
                self.notify("categories")
            await self._load_meat_types()
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def select_meat_type(self, meat_type: MeatType):
        self.selected_meat_type = meat_type
        self.notify("selected_meat_type")
        try:
            self.categories = await self.api.list_categories(meat_type_id=str(meat_type.id))
            self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _create_category(self):
        if not self.new_category_name or not self.selected_meat_type:
            return
        self.error = ""
        try:
            await self.api.create_category(str(self.selected_meat_type.id), self.new_category_name)
            self.new_category_name = ""
            self.notify("new_category_name")
            self.categories = await self.api.list_categories(meat_type_id=str(self.selected_meat_type.id))
            self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _update_category(self, category_id: str, name: str):
        self.error = ""
        try:
            await self.api.update_category(category_id, name)
            if self.selected_meat_type:
                self.categories = await self.api.list_categories(meat_type_id=str(self.selected_meat_type.id))
                self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _delete_category(self, category_id: str):
        self.error = ""
        logger.info(f"Deleting category: {category_id}")
        try:
            await self.api.delete_category(category_id)
            logger.info(f"Category deleted: {category_id}")
            if self.selected_meat_type:
                self.categories = await self.api.list_categories(meat_type_id=str(self.selected_meat_type.id))
                self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
