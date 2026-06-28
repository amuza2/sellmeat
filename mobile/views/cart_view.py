import flet as ft
import asyncio

from viewmodels.cart_viewmodel import CartViewModel
from components.ui import loading_indicator, error_text, empty_state, confirm_dialog, show_snackbar


class CartView:
    def __init__(self, page: ft.Page, vm: CartViewModel, on_order_placed, on_back):
        self.page = page
        self.vm = vm
        self.on_order_placed = on_order_placed
        self.on_back = on_back
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.items_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.slot_dropdown = ft.Dropdown(label="Créneau de livraison", width=300, on_select=self._on_slot_change)
        self.date_picker = ft.DatePicker(on_change=self._on_date_change)
        self.date_label = ft.Text("Aucune date sélectionnée", size=14, color=ft.Colors.GREY_600)
        self.date_button = ft.OutlinedButton(
            content=ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, size=18), self.date_label], spacing=8),
            on_click=self._open_date_picker,
        )
        self.notes_field = ft.TextField(label="Notes (optionnel)", multiline=True, max_lines=2, width=320)
        self.totals_column = ft.Column(spacing=4)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()
        self.place_button = ft.Button(
            "Passer la commande", on_click=lambda e: asyncio.create_task(self._on_place_order(e)), width=320, height=45,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )

        self.page.overlay.append(self.date_picker)

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Panier", size=24, weight=ft.FontWeight.BOLD),
                ]),
                self.loading_ctrl,
                self.error_ctrl,
                self.items_list,
                ft.Divider(),
                ft.Text("Livraison", size=16, weight=ft.FontWeight.W_500),
                self.slot_dropdown,
                self.date_button,
                self.notes_field,
                ft.Divider(),
                self.totals_column,
                self.place_button,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "items":
            self._render_items()
        elif prop == "delivery_slots":
            self._render_slots()
        elif prop == "delivery_fee":
            self._render_totals()
        elif prop == "error":
            self.error_ctrl.content = error_text(self.vm.error) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_indicator() if self.vm.is_loading else None
            self.place_button.disabled = self.vm.is_loading
        elif prop == "order_placed":
            if self.vm.order_placed:
                show_snackbar(self.page, "Commande passée avec succès !", 3000)
                self.on_order_placed()
        self.page.update()

    def _render_items(self):
        self.items_list.controls.clear()
        if not self.vm.items:
            self.items_list.controls.append(empty_state("Le panier est vide. Ajoutez des produits depuis le catalogue."))
            self._render_totals()
            return
        for i, item in enumerate(self.vm.items):
            unit_label = item.unit_label
            self.items_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column(
                            [
                                ft.Row([
                                    ft.Text(item.product.name, size=15, weight=ft.FontWeight.W_500),
                                    ft.Container(expand=True),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=20,
                                                  on_click=lambda e, idx=i, pn=item.product.name: confirm_dialog(self.page, "Remove Item", f"Remove '{pn}' from cart?", lambda: self._remove_item(idx))),
                                ]),
                                ft.Row([
                                    ft.Text(f"{item.quantity} {unit_label} x {item.product.price:.2f} DZD", size=12, color=ft.Colors.GREY_600),
                                    ft.Container(expand=True),
                                    ft.Text(f"{item.subtotal:.2f} DZD", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                ]),
                            ],
                            spacing=4,
                        ),
                    ),
                )
            )
        self._render_totals()

    def _render_slots(self):
        self.slot_dropdown.options = [
            ft.dropdown.Option(key=str(slot.id), text=f"{slot.label} ({slot.delivery_time.strftime('%H:%M')})")
            for slot in self.vm.delivery_slots
        ]

    def _render_totals(self):
        self.totals_column.controls = [
            ft.Row([ft.Text("Total articles :"), ft.Container(expand=True), ft.Text(f"{self.vm.items_total:.2f} DZD")]),
            ft.Row([ft.Text("Frais de livraison :"), ft.Container(expand=True), ft.Text(f"{self.vm.delivery_fee:.2f} DZD")]),
            ft.Divider(height=1),
            ft.Row([ft.Text("Total :", weight=ft.FontWeight.BOLD, size=18), ft.Container(expand=True),
                    ft.Text(f"{self.vm.total:.2f} DZD", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.RED_700)]),
        ]

    def _on_slot_change(self, e):
        for slot in self.vm.delivery_slots:
            if str(slot.id) == e.control.value:
                self.vm.selected_slot = slot
                self.vm.notify("selected_slot")
                break

    def _open_date_picker(self, e):
        self.date_picker.open = True
        self.page.update()

    def _on_date_change(self, e):
        self.vm.delivery_date = e.control.value
        self.date_label.value = f"Date : {e.control.value}"
        self.date_label.color = ft.Colors.GREEN_700
        self.date_label.weight = ft.FontWeight.W_500
        self.page.update()

    def _remove_item(self, index: int):
        self.vm.remove_item(index)

    async def _on_place_order(self, e):
        if not self.vm.items:
            return
        if not self.vm.selected_slot:
            show_snackbar(self.page, "Veuillez sélectionner un créneau de livraison")
            return
        if not self.vm.delivery_date:
            show_snackbar(self.page, "Veuillez sélectionner une date de livraison")
            return

        self.vm.notes = self.notes_field.value or ""

        item_rows = []
        for item in self.vm.items:
            item_rows.append(
                ft.Row([
                    ft.Text(f"{item.product.name} ({item.quantity} {item.unit_label})", size=13),
                    ft.Container(expand=True),
                    ft.Text(f"{item.subtotal:.2f} DZD", size=13),
                ])
            )

        async def _confirm(ev):
            self.page.pop_dialog()
            await self.vm.place_order_command()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmer la commande"),
                content=ft.Column([
                    ft.Text("Articles :", size=14, weight=ft.FontWeight.W_500),
                    *item_rows,
                    ft.Divider(height=1),
                    ft.Row([ft.Text("Total articles :"), ft.Container(expand=True), ft.Text(f"{self.vm.items_total:.2f} DZD")]),
                    ft.Row([ft.Text("Frais de livraison :"), ft.Container(expand=True), ft.Text(f"{self.vm.delivery_fee:.2f} DZD")]),
                    ft.Divider(height=1),
                    ft.Text(f"Livraison : {self.vm.selected_slot.label} le {self.vm.delivery_date}", size=13, color=ft.Colors.GREY_600),
                ], spacing=6, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Annuler"), on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton(content=ft.Text("Passer la commande", color=ft.Colors.RED), on_click=lambda e: asyncio.create_task(_confirm(e))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def render(self) -> ft.Control:
        self._render_items()
        self._render_slots()
        return self.content
