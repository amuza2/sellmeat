import httpx

from models.user import Token, User, UserCreate, UserLogin
from models.product import MeatType, Category, Product, ProductCreate, UnitType
from models.order import DeliverySlot, Order, OrderCreate, OrderStatus, PaymentStatus
from models.settings import AppSettings
from auth import Session

BASE_URL = "http://localhost:8000"


class APIClient:
    def __init__(self, session: Session):
        self.session = session
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        token = self.session.access_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> dict | list | None:
        resp = await self._client.request(method, path, headers=self._headers(), **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204:
            return None
        return resp.json()

    # --- Auth ---
    async def register(self, data: UserCreate) -> User:
        result = await self._request("POST", "/auth/register", json=data.model_dump(mode="json"))
        return User(**result)

    async def login(self, data: UserLogin) -> Token:
        result = await self._request("POST", "/auth/login", json=data.model_dump(mode="json"))
        return Token(**result)

    async def get_me(self) -> User:
        result = await self._request("GET", "/auth/me")
        return User(**result)

    # --- Meat Types ---
    async def list_meat_types(self) -> list[MeatType]:
        result = await self._request("GET", "/meat-types")
        return [MeatType(**m) for m in result]

    async def create_meat_type(self, name: str) -> MeatType:
        result = await self._request("POST", "/meat-types", json={"name": name})
        return MeatType(**result)

    async def update_meat_type(self, meat_type_id: str, name: str) -> MeatType:
        result = await self._request("PUT", f"/meat-types/{meat_type_id}", json={"name": name})
        return MeatType(**result)

    async def delete_meat_type(self, meat_type_id: str) -> None:
        await self._request("DELETE", f"/meat-types/{meat_type_id}")

    # --- Categories ---
    async def list_categories(self, meat_type_id: str | None = None) -> list[Category]:
        params = {}
        if meat_type_id:
            params["meat_type_id"] = meat_type_id
        result = await self._request("GET", "/categories", params=params)
        return [Category(**c) for c in result]

    async def create_category(self, meat_type_id: str, name: str) -> Category:
        result = await self._request("POST", "/categories", json={"meat_type_id": meat_type_id, "name": name})
        return Category(**result)

    async def update_category(self, category_id: str, name: str) -> Category:
        result = await self._request("PUT", f"/categories/{category_id}", json={"name": name})
        return Category(**result)

    async def delete_category(self, category_id: str) -> None:
        await self._request("DELETE", f"/categories/{category_id}")

    # --- Products ---
    async def list_products(self, category_id: str | None = None, meat_type_id: str | None = None) -> list[Product]:
        params = {}
        if category_id:
            params["category_id"] = category_id
        if meat_type_id:
            params["meat_type_id"] = meat_type_id
        result = await self._request("GET", "/products", params=params)
        return [Product(**p) for p in result]

    async def create_product(self, data: ProductCreate) -> Product:
        result = await self._request("POST", "/products", json=data.model_dump(mode="json"))
        return Product(**result)

    async def create_product_raw(self, data: dict) -> Product:
        result = await self._request("POST", "/products", json=data)
        return Product(**result)

    async def update_product(self, product_id: str, data: dict) -> Product:
        result = await self._request("PUT", f"/products/{product_id}", json=data)
        return Product(**result)

    async def delete_product(self, product_id: str) -> None:
        await self._request("DELETE", f"/products/{product_id}")

    # --- Delivery Slots ---
    async def list_delivery_slots(self, active_only: bool = False) -> list[DeliverySlot]:
        params = {}
        if active_only:
            params["active_only"] = "true"
        result = await self._request("GET", "/delivery-slots", params=params)
        return [DeliverySlot(**s) for s in result]

    async def create_delivery_slot(self, label: str, delivery_time: str, is_active: bool = True) -> DeliverySlot:
        result = await self._request("POST", "/delivery-slots", json={"label": label, "delivery_time": delivery_time, "is_active": is_active})
        return DeliverySlot(**result)

    async def update_delivery_slot(self, slot_id: str, data: dict) -> DeliverySlot:
        result = await self._request("PUT", f"/delivery-slots/{slot_id}", json=data)
        return DeliverySlot(**result)

    async def delete_delivery_slot(self, slot_id: str) -> None:
        await self._request("DELETE", f"/delivery-slots/{slot_id}")

    # --- Settings ---
    async def get_settings(self) -> AppSettings:
        result = await self._request("GET", "/settings")
        return AppSettings(**result)

    async def update_settings(self, delivery_fee: float) -> AppSettings:
        result = await self._request("PUT", "/settings", json={"delivery_fee": delivery_fee})
        return AppSettings(**result)

    # --- Orders ---
    async def list_orders(self) -> list[Order]:
        result = await self._request("GET", "/orders")
        return [Order(**o) for o in result]

    async def get_order(self, order_id: str) -> Order:
        result = await self._request("GET", f"/orders/{order_id}")
        return Order(**result)

    async def create_order(self, data: OrderCreate) -> Order:
        result = await self._request("POST", "/orders", json=data.model_dump(mode="json"))
        return Order(**result)

    async def update_order_status(self, order_id: str, status: OrderStatus) -> Order:
        result = await self._request("PUT", f"/orders/{order_id}/status", json={"status": status.value})
        return Order(**result)

    async def update_order_payment(self, order_id: str, payment_status: PaymentStatus) -> Order:
        result = await self._request("PUT", f"/orders/{order_id}/payment", json={"payment_status": payment_status.value})
        return Order(**result)

    async def update_order(self, order_id: str, data: dict) -> Order:
        result = await self._request("PUT", f"/orders/{order_id}", json=data)
        return Order(**result)

    async def add_order_item(self, order_id: str, product_id: str, quantity: float) -> Order:
        result = await self._request("POST", f"/orders/{order_id}/items", json={"product_id": product_id, "quantity": quantity})
        return Order(**result)

    async def remove_order_item(self, order_id: str, item_id: str) -> Order:
        result = await self._request("DELETE", f"/orders/{order_id}/items/{item_id}")
        return Order(**result)

    async def archive_order(self, order_id: str, archived: bool = True) -> Order:
        result = await self._request("PUT", f"/orders/{order_id}/archive", json={"is_archived": archived})
        return Order(**result)

    async def get_customer_orders(self, customer_id: str) -> list[Order]:
        result = await self._request("GET", f"/orders/customer/{customer_id}")
        return [Order(**o) for o in result]

    async def close(self):
        await self._client.aclose()
