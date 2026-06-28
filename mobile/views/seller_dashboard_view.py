import flet as ft
import asyncio

from viewmodels.seller_dashboard_viewmodel import SellerDashboardViewModel
from components.ui import loading_skeletons, error_with_retry, status_badge, payment_badge


class SellerDashboardView:
    def __init__(self, page: ft.Page, vm: SellerDashboardViewModel, on_navigate):
        self.page = page
        self.vm = vm
        self.on_navigate = on_navigate
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.stats_row = ft.Row(wrap=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        self.recent_list = ft.Column(spacing=6)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.summary_card = ft.Container()
        self.quick_actions = ft.Container()

        self.content = ft.Container(
            padding=16,
            expand=True,
            content=ft.Column(
            [
                ft.Text("Tableau de bord", size=24, weight=ft.FontWeight.BOLD),
                self.loading_ctrl,
                self.error_ctrl,
                self.stats_row,
                self.summary_card,
                self.quick_actions,
                ft.Divider(),
                ft.Row([
                    ft.Text("Commandes récentes", size=16, weight=ft.FontWeight.W_500),
                    ft.Container(expand=True),
                    ft.TextButton("Voir tout", on_click=lambda e: self.on_navigate("seller_orders")),
                ]),
                self.recent_list,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "orders":
            self._render_stats()
            self._render_recent()
        elif prop == "error":
            self.error_ctrl.content = error_with_retry(self.vm.error, self._retry) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_skeletons(3) if self.vm.is_loading else None
        self.page.update()

    def _retry(self, e=None):
        asyncio.create_task(self.vm.load_command())

    def _render_stats(self):
        self.stats_row.controls = [
            self._stat_card("En attente", self.vm.pending_count, ft.Colors.ORANGE),
            self._stat_card("Préparation", self.vm.preparation_count, ft.Colors.BLUE),
            self._stat_card("En livraison", self.vm.delivering_count, ft.Colors.PURPLE),
            self._stat_card("Livré", self.vm.delivered_count, ft.Colors.GREEN),
            self._stat_card("Non payé", self.vm.unpaid_count, ft.Colors.RED),
        ]

        self.summary_card.content = ft.Card(
            content=ft.Container(
                padding=14, expand=True,
                content=ft.Row([
                    ft.Column([
                        ft.Text("Revenu (livré)", size=12, color=ft.Colors.GREY_600),
                        ft.Text(f"{self.vm.total_revenue:.2f} DZD", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Column([
                        ft.Text("Total commandes", size=12, color=ft.Colors.GREY_600),
                        ft.Text(str(len(self.vm.orders)), size=20, weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ),
        )

        self.quick_actions.content = ft.Row([
            ft.Button("Nouvelles commandes", on_click=lambda e: self.on_navigate("seller_orders", "pending"), icon=ft.Icons.NEW_RELEASES, expand=True),
            ft.Button("Non payées", on_click=lambda e: self.on_navigate("seller_orders", "unpaid"), icon=ft.Icons.PAYMENTS, expand=True),
        ], spacing=8)

    def _stat_card(self, label: str, count: int, color) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                padding=10,
                width=100,
                content=ft.Column(
                    [ft.Text(str(count), size=24, weight=ft.FontWeight.BOLD, color=color),
                     ft.Text(label, size=11, color=ft.Colors.GREY_600)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2,
                ),
            ),
        )

    def _render_recent(self):
        self.recent_list.controls.clear()
        for order in self.vm.recent_orders:
            self.recent_list.controls.append(
                ft.Card(content=ft.Container(
                    padding=12,
                    on_click=lambda e, oid=str(order.id): self.on_navigate("order_detail", oid),
                    ink=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"#{str(order.id)[:8]}", size=14, weight=ft.FontWeight.W_500),
                            ft.Text(order.customer_name, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                            ft.Container(expand=True),
                            ft.Text(f"{order.total_amount:.2f} DZD", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                        ]),
                        ft.Row([
                            ft.Text(f"{order.delivery_slot_label} - {order.delivery_date}", size=12, color=ft.Colors.GREY_600),
                            ft.Container(expand=True),
                            status_badge(order.status.value),
                            payment_badge(order.payment_status.value),
                        ]),
                    ], spacing=4),
                ))
            )

    def render(self) -> ft.Control:
        return self.content
