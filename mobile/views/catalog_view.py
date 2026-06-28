import flet as ft
import asyncio

from viewmodels.catalog_viewmodel import CatalogViewModel
from components.ui import price_text, loading_skeletons, empty_state, error_with_retry, show_snackbar


class CatalogView:
    def __init__(self, page: ft.Page, vm: CatalogViewModel, on_add_to_cart, on_view_cart, cart_vm=None):
        self.page = page
        self.vm = vm
        self.on_add_to_cart = on_add_to_cart
        self.on_view_cart = on_view_cart
        self.cart_vm = cart_vm
        self.vm.add_listener(self._on_vm_changed)
        if self.cart_vm:
            self.cart_vm.add_listener(self._on_cart_changed)
        self._build()

    def _build(self):
        self.meat_type_row = ft.Row(wrap=True, spacing=8)
        self.category_row = ft.Row(wrap=True, spacing=8)
        self.products_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.refresh_btn = ft.TextButton("Actualiser", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(self._on_refresh()))

        self.cart_icon = ft.IconButton(ft.Icons.SHOPPING_CART, on_click=self._on_view_cart, icon_color=ft.Colors.RED_700)
        self.cart_badge_text = ft.Container(
            content=ft.Text(self._cart_count_text() or "", size=10, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
            visible=bool(self._cart_count_text()),
        )
        self.cart_badge = ft.Stack([
            self.cart_icon,
            ft.Container(
                content=self.cart_badge_text,
                right=0, top=0,
            ),
        ], width=40, height=40)

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Produits", size=24, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        self.cart_badge,
                    ],
                ),
                ft.Text("Types de viande", size=14, color=ft.Colors.GREY_600),
                self.meat_type_row,
                ft.Text("Catégories", size=14, color=ft.Colors.GREY_600),
                self.category_row,
                ft.Divider(),
                ft.Row([ft.Container(expand=True), self.refresh_btn]),
                self.loading_ctrl,
                self.error_ctrl,
                self.products_list,
            ],
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "meat_types":
            self._render_meat_types()
        elif prop == "categories":
            self._render_categories()
        elif prop == "products":
            self._render_products()
        elif prop == "error":
            self.error_ctrl.content = error_with_retry(self.vm.error, self._retry) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_skeletons(4) if self.vm.is_loading else None
        self.page.update()

    def _retry(self, e=None):
        asyncio.create_task(self.vm.load_meat_types_command())

    async def _on_refresh(self):
        await self.vm.load_meat_types_command()

    def _cart_count_text(self):
        if not self.cart_vm or not self.cart_vm.items:
            return None
        return str(len(self.cart_vm.items))

    def _on_cart_changed(self, prop: str):
        if prop == "items":
            count = self._cart_count_text()
            self.cart_badge_text.content.value = count or ""
            self.cart_badge_text.visible = bool(count)
            self.page.update()

    def _render_meat_types(self):
        self.meat_type_row.controls.clear()
        for mt in self.vm.meat_types:
            selected = self.vm.selected_meat_type and self.vm.selected_meat_type.id == mt.id
            self.meat_type_row.controls.append(
                ft.Chip(
                    label=ft.Text(mt.name),
                    selected=selected,
                    on_click=lambda e, m=mt: self._select_meat_type(m),
                )
            )

    def _render_categories(self):
        self.category_row.controls.clear()
        for cat in self.vm.categories:
            selected = self.vm.selected_category and self.vm.selected_category.id == cat.id
            self.category_row.controls.append(
                ft.Chip(
                    label=ft.Text(cat.name),
                    selected=selected,
                    on_click=lambda e, c=cat: self._select_category(c),
                )
            )

    def _render_products(self):
        self.products_list.controls.clear()
        if not self.vm.products:
            self.products_list.controls.append(empty_state("Sélectionnez une catégorie pour voir les produits"))
            return
        for product in self.vm.products:
            self.products_list.controls.append(self._product_card(product))

    def _product_card(self, product) -> ft.Card:
        qty_field = ft.TextField(
            label="Qté",
            value="1",
            width=70,
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        )

        def do_add(e):
            try:
                qty = float(qty_field.value or "0")
                if qty > 0:
                    self.on_add_to_cart(product, qty)
                    unit_label = "kg" if product.unit_type.value == "weight" else "unités"
                    show_snackbar(self.page, f"{qty} {unit_label} de {product.name} ajouté au panier")
            except ValueError:
                show_snackbar(self.page, "Quantité invalide")

        unit_label = "kg" if product.unit_type.value == "weight" else "unités"
        add_btn = ft.Button(
            "Ajouter", on_click=do_add, icon=ft.Icons.ADD_SHOPPING_CART,
            disabled=not product.is_available,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )
        return ft.Card(
            content=ft.Container(
                padding=14,
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(
                                ft.Icons.SHOPPING_BAG if product.is_available else ft.Icons.REMOVE_SHOPPING_CART,
                                size=28, color=ft.Colors.RED_400 if product.is_available else ft.Colors.GREY_400,
                            ),
                            ft.Column([
                                ft.Text(product.name, size=16, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    "Disponible" if product.is_available else "Rupture de stock",
                                    size=12,
                                    color=ft.Colors.GREEN_600 if product.is_available else ft.Colors.RED_600,
                                ),
                            ], spacing=2),
                            ft.Container(expand=True),
                            ft.Column([
                                ft.Text(f"{product.price:.0f} DZD", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                                ft.Text(f"par {unit_label}", size=11, color=ft.Colors.GREY_500),
                            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ]),
                        ft.Row([
                            ft.Container(expand=True),
                            qty_field,
                            add_btn,
                        ], spacing=8),
                    ],
                    spacing=10,
                ),
            ),
        )

    def _select_meat_type(self, meat_type):
        import asyncio
        asyncio.create_task(self.vm.select_meat_type(meat_type))

    def _select_category(self, category):
        import asyncio
        asyncio.create_task(self.vm.select_category(category))

    def _on_view_cart(self, e):
        self.on_view_cart()

    def render(self) -> ft.Control:
        return self.content
