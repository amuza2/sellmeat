from decimal import Decimal

from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.product import MeatType, Category, Product
from services.api import APIClient


class CatalogViewModel(ViewModelBase):
    meat_types = ObservableProperty([])
    categories = ObservableProperty([])
    products = ObservableProperty([])
    selected_meat_type = ObservableProperty(None)
    selected_category = ObservableProperty(None)
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_meat_types_command = AsyncCommand(self._load_meat_types)
        self.load_categories_command = AsyncCommand(self._load_categories)
        self.load_products_command = AsyncCommand(self._load_products)

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

    async def _load_categories(self):
        if not self.selected_meat_type:
            return
        try:
            self.categories = await self.api.list_categories(meat_type_id=str(self.selected_meat_type.id))
            self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _load_products(self):
        if not self.selected_category:
            return
        try:
            self.products = await self.api.list_products(category_id=str(self.selected_category.id))
            self.notify("products")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    def select_meat_type(self, meat_type: MeatType):
        self.selected_meat_type = meat_type
        self.selected_category = None
        self.products = []
        self.notify("selected_meat_type")
        return self._load_categories()

    def select_category(self, category: Category):
        self.selected_category = category
        self.notify("selected_category")
        return self._load_products()
