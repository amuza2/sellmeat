import flet as ft
import asyncio

from viewmodels.order_detail_viewmodel import OrderDetailViewModel
from models.order import OrderStatus, PaymentStatus
from components.ui import status_badge, payment_badge, loading_indicator, error_text, confirm_dialog, show_snackbar


class OrderDetailView:
    def __init__(self, page: ft.Page, vm: OrderDetailViewModel, on_back, is_seller: bool = False):
        self.page = page
        self.vm = vm
        self.on_back = on_back
        self.is_seller = is_seller
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.detail_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Détail de la commande", size=24, weight=ft.FontWeight.BOLD),
                ]),
                self.loading_ctrl,
                self.error_ctrl,
                self.detail_column,
            ],
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "order":
            self._render_detail()
        elif prop == "customer_history":
            self._show_history_dialog()
        elif prop == "error":
            self.error_ctrl.content = error_text(self.vm.error) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_indicator() if self.vm.is_loading else None
        self.page.update()

    def _render_detail(self):
        order = self.vm.order
        if not order:
            return
        self.detail_column.controls = []

        self.detail_column.controls.append(
            ft.Row([
                ft.Text(f"Commande #{str(order.id)[:8]}", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
            ])
        )
        self.detail_column.controls.append(
            ft.Row([
                status_badge(order.status.value),
                payment_badge(order.payment_status.value),
            ], spacing=8)
        )
        self.detail_column.controls.append(ft.Divider())

        self.detail_column.controls.append(ft.Text("Client", size=14, color=ft.Colors.GREY_600))
        customer_row = ft.Row([
            ft.Text(order.customer_name, size=16),
        ])
        if self.is_seller:
            customer_row.controls.append(
                ft.IconButton(
                    ft.Icons.INFO_OUTLINE, icon_size=18,
                    on_click=lambda e: self._show_customer_info(order),
                )
            )
        self.detail_column.controls.append(customer_row)

        self.detail_column.controls.append(ft.Text("Livraison", size=14, color=ft.Colors.GREY_600))
        self.detail_column.controls.append(
            ft.Text(f"{order.delivery_slot_label} à {order.delivery_slot_time or 'N/A'} le {order.delivery_date}", size=16)
        )

        if order.notes:
            self.detail_column.controls.append(ft.Text("Notes", size=14, color=ft.Colors.GREY_600))
            self.detail_column.controls.append(ft.Text(order.notes, size=14))

        self.detail_column.controls.append(ft.Divider())
        items_header = ft.Row([
            ft.Text("Articles", size=16, weight=ft.FontWeight.W_500),
            ft.Container(expand=True),
        ])
        if self.is_seller:
            items_header.controls.append(
                ft.TextButton("Ajouter un article", icon=ft.Icons.ADD, on_click=self._open_add_item_dialog)
            )
        self.detail_column.controls.append(items_header)

        for item in order.items:
            unit_label = "kg" if item.unit_type.value == "weight" else "unités"
            if self.is_seller:
                item_row = ft.Card(content=ft.Container(padding=12, content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(item.product_name, size=14, weight=ft.FontWeight.W_500),
                            ft.Text(f"{item.quantity} {unit_label} x {item.unit_price:.2f} DZD", size=12, color=ft.Colors.GREY_600),
                        ], spacing=2, expand=True),
                        ft.Text(f"{item.subtotal:.2f} DZD", size=14, weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Container(expand=True),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=18,
                                      on_click=lambda ev, iid=str(item.id), iname=item.product_name: confirm_dialog(self.page, "Retirer l'article", f"Retirer '{iname}' de la commande ?", lambda: asyncio.create_task(self.vm.remove_item_command(iid)))),
                    ]),
                ], spacing=4)))
            else:
                item_row = ft.Card(content=ft.Container(padding=12, content=ft.Row([
                    ft.Column([
                        ft.Text(item.product_name, size=14, weight=ft.FontWeight.W_500),
                        ft.Text(f"{item.quantity} {unit_label} x {item.unit_price:.2f} DZD", size=12, color=ft.Colors.GREY_600),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Text(f"{item.subtotal:.2f} DZD", size=14, weight=ft.FontWeight.BOLD),
                ])))
            self.detail_column.controls.append(item_row)

        self.detail_column.controls.append(ft.Divider())
        self.detail_column.controls.append(ft.Row([ft.Text("Total articles :"), ft.Container(expand=True), ft.Text(f"{order.items_total:.2f} DZD")]))
        self.detail_column.controls.append(ft.Row([ft.Text("Frais de livraison :"), ft.Container(expand=True), ft.Text(f"{order.delivery_fee:.2f} DZD")]))
        self.detail_column.controls.append(ft.Divider(height=1))
        self.detail_column.controls.append(ft.Row([ft.Text("Total :", weight=ft.FontWeight.BOLD, size=18), ft.Container(expand=True),
                                                    ft.Text(f"{order.total_amount:.2f} DZD", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.RED_700)]))

        if self.is_seller:
            self.detail_column.controls.append(ft.Divider())
            self.detail_column.controls.append(ft.Text("Actions du vendeur", size=16, weight=ft.FontWeight.W_500))

            status_labels = {"pending": "En attente", "preparation": "Préparation", "delivering": "En livraison", "delivered": "Livré", "cancelled": "Annulé"}
            status_options = [s.value for s in OrderStatus]
            self.detail_column.controls.append(
                ft.Row([ft.Text("Statut :"), ft.Container(expand=True),
                        ft.Dropdown(
                            value=order.status.value,
                            options=[ft.dropdown.Option(s, status_labels.get(s, s)) for s in status_options],
                            on_select=lambda e: asyncio.create_task(self._on_status_change(e)),
                            width=180,
                        )])
            )

            payment_labels = {"paid": "Payé", "unpaid": "Non payé"}
            self.detail_column.controls.append(
                ft.Row([ft.Text("Paiement :"), ft.Container(expand=True),
                        ft.Dropdown(
                            value=order.payment_status.value,
                            options=[ft.dropdown.Option(p.value, payment_labels.get(p.value, p.value)) for p in PaymentStatus],
                            on_select=lambda e: asyncio.create_task(self._on_payment_change(e)),
                            width=180,
                        )])
            )

            self.detail_column.controls.append(
                ft.Row([
                    ft.Button(
                        "Modifier la commande",
                        on_click=self._open_edit_dialog,
                        icon=ft.Icons.EDIT,
                        expand=True,
                    ),
                    ft.Button(
                        "Historique du client",
                        on_click=lambda e: asyncio.create_task(self._load_history()),
                        icon=ft.Icons.HISTORY,
                        expand=True,
                    ),
                ], spacing=8)
            )

            archive_label = "Désarchiver" if order.is_archived else "Archiver"
            self.detail_column.controls.append(
                ft.Button(
                    archive_label,
                    on_click=lambda e: asyncio.create_task(self._on_archive(order)),
                    icon=ft.Icons.ARCHIVE,
                    width=320,
                )
            )

    async def _on_archive(self, order):
        await self.vm.archive_order_command(str(order.id), not order.is_archived)
        self.on_back()

    async def _copy_to_clipboard(self, text):
        import re
        clean = re.sub(r'[^\d+]', '', text)
        await self.page.clipboard.set(clean)
        show_snackbar(self.page, "Numéro de téléphone copié", 1500)

    def _show_customer_info(self, order):
        phone = order.customer_phone or "N/A"
        info_rows = [
            ft.Row([ft.Icon(ft.Icons.PERSON, size=18, color=ft.Colors.GREY_600), ft.Text(order.customer_name, size=14)]),
            ft.Row([ft.Icon(ft.Icons.EMAIL, size=18, color=ft.Colors.GREY_600), ft.Text(order.customer_email or "N/A", size=14)]),
            ft.Row([
                ft.Icon(ft.Icons.PHONE, size=18, color=ft.Colors.GREY_600),
                ft.Text(phone, size=14),
                ft.IconButton(
                    ft.Icons.CONTENT_COPY, icon_size=16,
                    on_click=lambda e: asyncio.create_task(self._copy_to_clipboard(phone)),
                ),
            ]),
        ]
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Détails du client"),
                content=ft.Column(info_rows, spacing=12, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Fermer"), on_click=lambda e: self.page.pop_dialog()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    async def _on_status_change(self, e):
        await self.vm.update_status_command(OrderStatus(e.control.value))

    async def _on_payment_change(self, e):
        await self.vm.update_payment_command(PaymentStatus(e.control.value))

    def _open_edit_dialog(self, e):
        order = self.vm.order
        if not order:
            return

        slot_dropdown = ft.Dropdown(
            label="Créneau de livraison", width=300, dense=True,
            value=str(order.delivery_slot_id),
        )
        date_field = ft.TextField(
            label="Date de livraison (AAAA-MM-JJ)", width=300, dense=True,
            value=str(order.delivery_date),
        )
        notes_field = ft.TextField(
            label="Notes", width=300, dense=True, multiline=True, min_lines=2,
            value=order.notes or "",
        )

        async def _load_slots():
            try:
                slots = await self.vm.api.list_delivery_slots()
                slot_dropdown.options = [
                    ft.dropdown.Option(key=str(s.id), text=f"{s.label} ({s.delivery_time.strftime('%H:%M')})")
                    for s in slots
                ]
                self.page.update()
            except Exception:
                pass

        asyncio.create_task(_load_slots())

        async def _save(ev):
            data = {}
            if slot_dropdown.value and slot_dropdown.value != str(order.delivery_slot_id):
                data["delivery_slot_id"] = slot_dropdown.value
            if date_field.value and date_field.value != str(order.delivery_date):
                data["delivery_date"] = date_field.value
            if notes_field.value != (order.notes or ""):
                data["notes"] = notes_field.value or None
            self.page.pop_dialog()
            if data:
                await self.vm.update_order_command(data)

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Modifier la commande"),
                content=ft.Column([
                    slot_dropdown,
                    date_field,
                    notes_field,
                ], spacing=10, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Annuler"), on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton(content=ft.Text("Enregistrer", color=ft.Colors.RED), on_click=lambda e: asyncio.create_task(_save(e))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _open_add_item_dialog(self, e):
        product_dropdown = ft.Dropdown(label="Produit", width=300, dense=True)
        qty_field = ft.TextField(label="Quantité", width=300, dense=True, keyboard_type=ft.KeyboardType.NUMBER, value="1")

        async def _load_products():
            try:
                products = await self.vm.api.list_products()
                product_dropdown.options = [
                    ft.dropdown.Option(key=str(p.id), text=f"{p.name} ({p.price:.2f} DZD)")
                    for p in products if p.is_available
                ]
                self.page.update()
            except Exception:
                pass

        asyncio.create_task(_load_products())

        async def _add(ev):
            if not product_dropdown.value or not qty_field.value:
                return
            self.page.pop_dialog()
            await self.vm.add_item_command(product_dropdown.value, float(qty_field.value))

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Ajouter un article à la commande"),
                content=ft.Column([
                    product_dropdown,
                    qty_field,
                ], spacing=10, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Annuler"), on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton(content=ft.Text("Ajouter", color=ft.Colors.RED), on_click=lambda e: asyncio.create_task(_add(e))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    async def _load_history(self):
        await self.vm.load_customer_history_command()

    def _show_history_dialog(self):
        orders = self.vm.customer_history
        if not orders:
            self.page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Historique du client"),
                    content=ft.Text("Aucune commande antérieure trouvée pour ce client."),
                    actions=[ft.TextButton(content=ft.Text("Fermer"), on_click=lambda e: self.page.pop_dialog())],
                )
            )
            return

        history_items = []
        for o in orders:
            history_items.append(
                ft.Card(content=ft.Container(padding=10, content=ft.Column([
                    ft.Row([
                        ft.Text(f"#{str(o.id)[:8]}", size=13, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.Text(f"{o.total_amount:.2f} DZD", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                    ]),
                    ft.Row([
                        ft.Text(f"{o.delivery_date}", size=11, color=ft.Colors.GREY_600),
                        ft.Container(expand=True),
                        status_badge(o.status.value),
                        payment_badge(o.payment_status.value),
                    ]),
                ], spacing=4)))
            )

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Historique du client ({self.vm.order.customer_name})"),
                content=ft.Container(
                    width=400,
                    content=ft.Column(history_items, spacing=6, scroll=ft.ScrollMode.AUTO, height=400),
                ),
                actions=[ft.TextButton(content=ft.Text("Fermer"), on_click=lambda e: self.page.pop_dialog())],
            )
        )

    def render(self) -> ft.Control:
        return self.content
