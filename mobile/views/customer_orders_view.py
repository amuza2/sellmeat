import flet as ft
import asyncio

from viewmodels.customer_orders_viewmodel import CustomerOrdersViewModel
from models.order import OrderStatus
from components.ui import status_badge, payment_badge, loading_skeletons, empty_state, error_with_retry


class CustomerOrdersView:
    def __init__(self, page: ft.Page, vm: CustomerOrdersViewModel, on_order_click, on_back):
        self.page = page
        self.vm = vm
        self.on_order_click = on_order_click
        self.on_back = on_back
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.orders_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.refresh_btn = ft.TextButton("Actualiser", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(self._on_refresh()))

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Mes commandes", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    self.refresh_btn,
                ]),
                self.loading_ctrl,
                self.error_ctrl,
                self.orders_list,
            ],
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "orders":
            self._render_orders()
        elif prop == "error":
            self.error_ctrl.content = error_with_retry(self.vm.error, self._retry) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_skeletons(4) if self.vm.is_loading else None
        self.page.update()

    def _retry(self, e=None):
        asyncio.create_task(self.vm.load_orders_command())

    async def _on_refresh(self):
        await self.vm.load_orders_command()

    def _render_orders(self):
        self.orders_list.controls.clear()
        if not self.vm.orders:
            self.orders_list.controls.append(empty_state("Aucune commande. Passez votre première commande !"))
            return
        for order in self.vm.orders:
            self.orders_list.controls.append(self._order_card(order))

    def _order_card(self, order) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                padding=14,
                on_click=lambda e, oid=str(order.id): self.on_order_click(oid),
                ink=True,
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Text(f"Commande #{str(order.id)[:8]}", size=15, weight=ft.FontWeight.W_500),
                            ft.Container(expand=True),
                            ft.Text(f"{order.total_amount:.2f} DZD", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                        ]),
                        ft.Text(f"Livraison : {order.delivery_slot_label} - {order.delivery_date}", size=12, color=ft.Colors.GREY_600),
                        ft.Row([
                            ft.Text(f"{len(order.items)} articles", size=13, color=ft.Colors.GREY_700),
                        ]),
                        ft.Row([
                            status_badge(order.status.value),
                            payment_badge(order.payment_status.value),
                        ], spacing=8),
                    ],
                    spacing=6,
                ),
            ),
        )

    def render(self) -> ft.Control:
        return self.content
