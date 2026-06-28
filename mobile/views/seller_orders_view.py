import flet as ft
import asyncio

from viewmodels.seller_orders_viewmodel import SellerOrdersViewModel
from models.order import OrderStatus, PaymentStatus
from components.ui import status_badge, payment_badge, loading_skeletons, empty_state, error_with_retry


class SellerOrdersView:
    def __init__(self, page: ft.Page, vm: SellerOrdersViewModel, on_order_click, on_back):
        self.page = page
        self.vm = vm
        self.on_order_click = on_order_click
        self.on_back = on_back
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.orders_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.refresh_btn = ft.TextButton("Actualiser", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(self._on_refresh()))

        self.status_filter = ft.Dropdown(
            label="Filtrer par statut", expand=True,
            options=[ft.dropdown.Option("all", "Tous")] + [ft.dropdown.Option(s.value, {"pending": "En attente", "preparation": "Préparation", "delivering": "En livraison", "delivered": "Livré", "cancelled": "Annulé"}.get(s.value, s.value.title())) for s in OrderStatus],
            value="all",
            on_select=self._on_filter_change,
        )
        self.payment_filter = ft.Dropdown(
            label="Filtrer par paiement", expand=True,
            options=[ft.dropdown.Option("all", "Tous"), ft.dropdown.Option("paid", "Payé"), ft.dropdown.Option("unpaid", "Non payé")],
            value="all",
            on_select=self._on_filter_change,
        )

        self.show_archived_switch = ft.Switch(
            label="Afficher archivées", value=False,
            on_change=self._on_archived_toggle,
        )

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Commandes", size=24, weight=ft.FontWeight.BOLD),
                ]),
                ft.Row([self.status_filter, self.payment_filter], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.show_archived_switch, ft.Container(expand=True), self.refresh_btn]),
                self.loading_ctrl,
                self.error_ctrl,
                self.orders_list,
            ],
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop in ("orders", "status_filter", "payment_filter", "show_archived"):
            self._render_orders()
        elif prop == "error":
            self.error_ctrl.content = error_with_retry(self.vm.error, self._retry) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_skeletons(4) if self.vm.is_loading else None
        self.page.update()

    def _on_archived_toggle(self, e):
        self.vm.show_archived = e.control.value
        self.vm.notify("show_archived")

    def _retry(self, e=None):
        asyncio.create_task(self.vm.load_orders_command())

    async def _on_refresh(self):
        await self.vm.load_orders_command()

    def _on_filter_change(self, e):
        status_val = self.status_filter.value
        payment_val = self.payment_filter.value
        self.vm.status_filter = OrderStatus(status_val) if status_val and status_val != "all" else None
        self.vm.payment_filter = PaymentStatus(payment_val) if payment_val and payment_val != "all" else None
        self.vm.notify("status_filter")

    def _render_orders(self):
        self.status_filter.value = self.vm.status_filter.value if self.vm.status_filter else "all"
        self.payment_filter.value = self.vm.payment_filter.value if self.vm.payment_filter else "all"
        self.orders_list.controls.clear()
        orders = self.vm.filtered_orders
        if not orders:
            self.orders_list.controls.append(empty_state("Aucune commande trouvée"))
            return
        for order in orders:
            self.orders_list.controls.append(self._order_card(order))

    def _order_card(self, order) -> ft.Card:
        badges = [status_badge(order.status.value), payment_badge(order.payment_status.value)]
        if order.is_archived:
            badges.insert(0, ft.Container(
                content=ft.Text("ARCHIVÉE", size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.GREY,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
            ))
        return ft.Card(
            content=ft.Container(
                padding=12,
                on_click=lambda e, oid=str(order.id): self.on_order_click(oid),
                ink=True,
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"#{str(order.id)[:8]}", size=14, weight=ft.FontWeight.W_500),
                        ft.Text(order.customer_name, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        ft.Container(expand=True),
                        ft.Text(f"{order.total_amount:.2f} DZD", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                    ]),
                    ft.Text(f"{order.delivery_slot_label} - {order.delivery_date}", size=12, color=ft.Colors.GREY_600),
                    ft.Row([
                        ft.Text(f"{len(order.items)} articles", size=13, color=ft.Colors.GREY_700),
                    ]),
                    ft.Row(badges, spacing=8),
                ], spacing=4),
            ),
        )

    def render(self) -> ft.Control:
        return self.content
