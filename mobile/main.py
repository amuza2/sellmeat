import asyncio
from decimal import Decimal

import flet as ft

from auth import Session
from services.api import APIClient
from models.order import OrderStatus, PaymentStatus
from viewmodels.auth_viewmodel import AuthViewModel
from viewmodels.catalog_viewmodel import CatalogViewModel
from viewmodels.cart_viewmodel import CartViewModel, CartItem
from viewmodels.customer_orders_viewmodel import CustomerOrdersViewModel
from viewmodels.order_detail_viewmodel import OrderDetailViewModel
from viewmodels.seller_dashboard_viewmodel import SellerDashboardViewModel
from viewmodels.seller_orders_viewmodel import SellerOrdersViewModel
from viewmodels.manage_meat_viewmodel import ManageMeatViewModel
from viewmodels.manage_products_viewmodel import ManageProductsViewModel
from viewmodels.manage_slots_viewmodel import ManageSlotsViewModel
from viewmodels.manage_settings_viewmodel import ManageSettingsViewModel
from views.auth_view import AuthView
from views.catalog_view import CatalogView
from views.cart_view import CartView
from views.customer_orders_view import CustomerOrdersView
from views.order_detail_view import OrderDetailView
from views.seller_dashboard_view import SellerDashboardView
from views.seller_orders_view import SellerOrdersView
from views.manage_products_view import ManageProductsView
from views.manage_settings_view import ManageSettingsView


def main(page: ft.Page):
    page.title = "SellMeat"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.RED)

    session = Session()
    api = APIClient(session)

    # Shared cart items across catalog and cart views
    cart_items: list[CartItem] = []

    # ViewModels
    auth_vm = AuthViewModel(api, session)
    catalog_vm = CatalogViewModel(api)
    cart_vm = CartViewModel(api)
    customer_orders_vm = CustomerOrdersViewModel(api)
    order_detail_vm = OrderDetailViewModel(api)
    seller_dashboard_vm = SellerDashboardViewModel(api)
    seller_orders_vm = SellerOrdersViewModel(api)
    manage_meat_vm = ManageMeatViewModel(api)
    manage_products_vm = ManageProductsViewModel(api)
    manage_slots_vm = ManageSlotsViewModel(api)
    manage_settings_vm = ManageSettingsViewModel(api)

    current_view = None

    def navigate(route: str, *args):
        nonlocal current_view
        page.views.clear()

        customer_routes = ["catalog", "cart", "orders"]
        seller_routes = ["seller_dashboard", "seller_orders", "manage_meat", "manage_products", "manage_slots"]

        if route == "auth":
            auth_vm.reset()
            cart_vm.clear()
            view = AuthView(page, auth_vm, on_auth_success).render()
            page.views.append(ft.View(route="/", controls=[view]))
        elif route == "catalog":
            nav = _build_customer_nav(0)
            view = CatalogView(page, catalog_vm, on_add_to_cart, lambda: navigate("cart"), cart_vm).render()
            page.views.append(ft.View(route="/catalog", controls=[view], navigation_bar=nav))
        elif route == "cart":
            nav = _build_customer_nav(1)
            view = CartView(page, cart_vm, lambda: navigate("orders"), lambda: navigate("catalog")).render()
            page.views.append(ft.View(route="/cart", controls=[view], navigation_bar=nav))
        elif route == "orders":
            nav = _build_customer_nav(2)
            view = CustomerOrdersView(page, customer_orders_vm, lambda oid: navigate("order_detail", oid), lambda: navigate("catalog")).render()
            page.views.append(ft.View(route="/orders", controls=[view], navigation_bar=nav))
        elif route == "customer_settings":
            nav = _build_customer_nav(3)
            view = ManageSettingsView(page, manage_settings_vm, lambda: navigate("catalog"), session, lambda: navigate("auth")).render()
            page.views.append(ft.View(route="/customer_settings", controls=[view], navigation_bar=nav))
        elif route == "order_detail":
            is_seller = session.is_seller
            nav = _build_nav_for_role(1 if is_seller else 2)
            view = OrderDetailView(page, order_detail_vm, lambda: navigate("orders" if not is_seller else "seller_orders"), is_seller).render()
            page.views.append(ft.View(route="/order_detail", controls=[view], navigation_bar=nav))
        elif route == "seller_dashboard":
            nav = _build_seller_nav(0)
            view = SellerDashboardView(page, seller_dashboard_vm, lambda r, *a: navigate(r, *a)).render()
            page.views.append(ft.View(route="/seller_dashboard", controls=[view], navigation_bar=nav))
        elif route == "seller_orders":
            nav = _build_seller_nav(1)
            if args and args[0] == "pending":
                seller_orders_vm.set_filters(status=OrderStatus.pending)
            elif args and args[0] == "unpaid":
                seller_orders_vm.set_filters(payment=PaymentStatus.unpaid)
            else:
                seller_orders_vm.set_filters()
            view = SellerOrdersView(page, seller_orders_vm, lambda oid: navigate("order_detail", oid), lambda: navigate("seller_dashboard")).render()
            page.views.append(ft.View(route="/seller_orders", controls=[view], navigation_bar=nav))
        elif route == "manage_products":
            nav = _build_seller_nav(2)
            view = ManageProductsView(page, manage_products_vm, lambda: navigate("seller_dashboard"), meat_vm=manage_meat_vm).render()
            page.views.append(ft.View(route="/manage_products", controls=[view], navigation_bar=nav))
        elif route == "manage_settings":
            nav = _build_seller_nav(3)
            view = ManageSettingsView(page, manage_settings_vm, lambda: navigate("seller_dashboard"), session, lambda: navigate("auth"), slots_vm=manage_slots_vm).render()
            page.views.append(ft.View(route="/manage_settings", controls=[view], navigation_bar=nav))
        else:
            page.views.append(ft.View(route="/", controls=[ft.Text("Unknown route")]))

        page.update()

        # Load data after view is rendered
        if route == "catalog":
            asyncio.create_task(catalog_vm.load_meat_types_command())
        elif route == "cart":
            asyncio.create_task(cart_vm.load_slots_command())
        elif route == "orders":
            asyncio.create_task(customer_orders_vm.load_orders_command())
        elif route == "seller_dashboard":
            asyncio.create_task(seller_dashboard_vm.load_command())
        elif route == "seller_orders":
            asyncio.create_task(seller_orders_vm.load_orders_command())
        elif route == "order_detail":
            asyncio.create_task(order_detail_vm.load_order_command(args[0]))
        elif route == "manage_products":
            asyncio.create_task(manage_products_vm.load_meat_types_command())
            asyncio.create_task(manage_products_vm.load_products_command())
        elif route == "manage_settings":
            asyncio.create_task(manage_settings_vm.load_command())
            asyncio.create_task(manage_slots_vm.load_command())
        elif route == "customer_settings":
            asyncio.create_task(manage_settings_vm.load_command())

    def on_auth_success():
        if session.is_seller:
            navigate("seller_dashboard")
        else:
            navigate("catalog")

    def on_add_to_cart(product, quantity):
        cart_vm.add_item(product, Decimal(str(quantity)))

    def _build_customer_nav(selected_index: int) -> ft.NavigationBar:
        return ft.NavigationBar(
            selected_index=selected_index,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.STORE_OUTLINED, selected_icon=ft.Icons.STORE, label="Catalogue"),
                ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART_OUTLINED, selected_icon=ft.Icons.SHOPPING_CART, label="Panier"),
                ft.NavigationBarDestination(icon=ft.Icons.LIST_OUTLINED, selected_icon=ft.Icons.LIST, label="Commandes"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Paramètres"),
            ],
            on_change=lambda e: navigate(["catalog", "cart", "orders", "customer_settings"][e.control.selected_index]),
        )

    def _build_seller_nav(selected_index: int) -> ft.NavigationBar:
        return ft.NavigationBar(
            selected_index=selected_index,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Tableau de bord"),
                ft.NavigationBarDestination(icon=ft.Icons.LIST_OUTLINED, selected_icon=ft.Icons.LIST, label="Commandes"),
                ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_OUTLINED, selected_icon=ft.Icons.INVENTORY, label="Produits"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Paramètres"),
            ],
            on_change=lambda e: navigate(["seller_dashboard", "seller_orders", "manage_products", "manage_settings"][e.control.selected_index]),
        )

    def _build_nav_for_role(selected_index: int) -> ft.NavigationBar:
        if session.is_seller:
            return _build_seller_nav(selected_index)
        return _build_customer_nav(selected_index)

    # Start at auth screen or restore session
    if session.is_authenticated:
        if session.is_seller:
            navigate("seller_dashboard")
        else:
            navigate("catalog")
    else:
        navigate("auth")


if __name__ == "__main__":
    ft.run(main)
