from decimal import Decimal

from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.product import Product, UnitType
from services.api import APIClient


class ManageProductsViewModel(ViewModelBase):
    products = ObservableProperty([])
    categories = ObservableProperty([])
    meat_types = ObservableProperty([])
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    new_name = ObservableProperty("")
    new_price = ObservableProperty("")
    new_unit_type = ObservableProperty(UnitType.weight)
    new_is_available = ObservableProperty(True)
    selected_category_id = ObservableProperty(None)

    def __init__(self, api: APIClient):
        super().__init__()
        self.api = api
        self.load_products_command = AsyncCommand(self._load_products)
        self.create_product_command = AsyncCommand(self._create_product)
        self.delete_product_command = AsyncCommand(self._delete_product)
        self.toggle_availability_command = AsyncCommand(self._toggle_availability)
        self.load_categories_command = AsyncCommand(self._load_categories)
        self.load_meat_types_command = AsyncCommand(self._load_meat_types)
        self.update_product_command = AsyncCommand(self._update_product)

    async def _load_meat_types(self):
        try:
            self.meat_types = await self.api.list_meat_types()
            self.notify("meat_types")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _load_categories_by_meat(self, meat_type_id: str):
        try:
            self.categories = await self.api.list_categories(meat_type_id=meat_type_id)
            self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _load_categories(self):
        try:
            self.categories = await self.api.list_categories()
            self.notify("categories")
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _load_products(self, category_id: str | None = None, meat_type_id: str | None = None):
        self.is_loading = True
        self.notify("is_loading")
        try:
            self.products = await self.api.list_products(category_id=category_id, meat_type_id=meat_type_id)
            self.notify("products")
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _create_product(self):
        if not self.new_name or not self.new_price or not self.selected_category_id:
            return
        try:
            data = {
                "category_id": str(self.selected_category_id),
                "name": self.new_name,
                "unit_type": self.new_unit_type.value,
                "price": float(self.new_price),
                "is_available": self.new_is_available,
            }
            await self.api.create_product_raw(data)
            self.new_name = ""
            self.new_price = ""
            self.notify("new_name")
            self.notify("new_price")
            await self._load_products(str(self.selected_category_id) if self.selected_category_id else None)
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _delete_product(self, product_id: str):
        try:
            await self.api.delete_product(product_id)
            cat_id = str(self.selected_category_id) if self.selected_category_id else None
            await self._load_products(cat_id)
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _toggle_availability(self, product: Product):
        try:
            await self.api.update_product(str(product.id), {"is_available": not product.is_available})
            cat_id = str(self.selected_category_id) if self.selected_category_id else None
            await self._load_products(cat_id)
        except Exception as e:
            self.error = str(e)
            self.notify("error")

    async def _update_product(self, product_id: str, data: dict):
        try:
            await self.api.update_product(product_id, data)
            cat_id = str(self.selected_category_id) if self.selected_category_id else None
            mt_id = self.meat_type_filter_value if hasattr(self, 'meat_type_filter_value') else None
            await self._load_products(cat_id, meat_type_id=mt_id)
        except Exception as e:
            self.error = str(e)
            self.notify("error")
