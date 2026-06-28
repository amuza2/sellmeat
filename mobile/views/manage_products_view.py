import flet as ft
import asyncio

from viewmodels.manage_products_viewmodel import ManageProductsViewModel
from viewmodels.manage_meat_viewmodel import ManageMeatViewModel
from models.product import UnitType
from components.ui import loading_skeletons, empty_state, error_with_retry, price_text, confirm_dialog


class ManageProductsView:
    def __init__(self, page: ft.Page, vm: ManageProductsViewModel, on_back, meat_vm: ManageMeatViewModel = None):
        self.page = page
        self.vm = vm
        self.on_back = on_back
        self.meat_vm = meat_vm
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.products_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.refresh_btn = ft.TextButton("Actualiser", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(self._on_refresh()))

        self.meat_type_filter = ft.Dropdown(label="Filtrer par type de viande", width=300, dense=True, on_select=self._on_meat_type_filter)
        self.category_filter = ft.Dropdown(label="Filtrer par catégorie", width=300, dense=True, disabled=True, on_select=self._on_category_change)

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Produits", size=22, weight=ft.FontWeight.BOLD),
                ]),
                self.meat_type_filter,
                self.category_filter,
                ft.Row([
                    ft.Button("Ajouter un produit", on_click=self._open_add_dialog, icon=ft.Icons.ADD, width=145),
                    ft.Button("Types de viande", on_click=self._open_meat_dialog, icon=ft.Icons.CATEGORY, width=145),
                ], spacing=8),
                ft.Divider(),
                ft.Row([ft.Container(expand=True), self.refresh_btn]),
                self.loading_ctrl,
                self.error_ctrl,
                self.products_list,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ))

    def set_categories(self, categories):
        self.category_filter.options = [
            ft.dropdown.Option(key=str(cat.id), text=cat.name)
            for cat in categories
        ]

    def set_meat_types(self, meat_types):
        self.meat_type_filter.options = [
            ft.dropdown.Option(key=str(mt.id), text=mt.name)
            for mt in meat_types
        ]

    def _on_vm_changed(self, prop: str):
        if prop == "products":
            self._render_products()
        elif prop == "categories":
            self.set_categories(self.vm.categories)
        elif prop == "meat_types":
            self.set_meat_types(self.vm.meat_types)
        elif prop == "error":
            self.error_ctrl.content = error_with_retry(self.vm.error, self._retry) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_skeletons(4) if self.vm.is_loading else None
        self.page.update()

    def _retry(self, e=None):
        asyncio.create_task(self.vm.load_meat_types_command())
        asyncio.create_task(self.vm.load_products_command())

    async def _on_refresh(self):
        await self.vm.load_meat_types_command()
        await self.vm.load_products_command()

    def _render_products(self):
        self.products_list.controls.clear()
        if not self.vm.products:
            self.products_list.controls.append(empty_state("Aucun produit. Sélectionnez une catégorie et ajoutez-en un."))
            return
        for product in self.vm.products:
            self.products_list.controls.append(
                ft.Card(content=ft.Container(padding=12, content=ft.Column([
                    ft.Row([
                        ft.Text(product.name, size=14, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE, icon_size=20,
                                      on_click=lambda e, p=product: self._open_edit_dialog(p)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=20,
                                      on_click=lambda e, pid=str(product.id), pn=product.name: confirm_dialog(self.page, "Supprimer le produit", f"Supprimer '{pn}' ?", lambda: asyncio.create_task(self._delete(pid)))),
                    ]),
                    ft.Row([
                        price_text(product.price, product.unit_type.value),
                        ft.Container(expand=True),
                        ft.Switch(
                            label="Disponible", value=product.is_available,
                            on_change=lambda e, p=product: asyncio.create_task(self._toggle_avail(p)),
                        ),
                    ]),
                ], spacing=4)))
            )

    def _on_meat_type_filter(self, e):
        meat_type_id = e.control.value
        self.category_filter.disabled = False
        self.category_filter.value = None
        self.category_filter.options = []
        self.vm.selected_category_id = None
        if meat_type_id:
            asyncio.create_task(self.vm._load_categories_by_meat(meat_type_id))
            asyncio.create_task(self.vm._load_products(meat_type_id=meat_type_id))
        else:
            asyncio.create_task(self.vm._load_products())
        self.page.update()

    def _on_category_change(self, e):
        self.vm.selected_category_id = e.control.value
        self.vm.notify("selected_category_id")
        asyncio.create_task(self.vm.load_products_command(e.control.value))

    def _open_meat_dialog(self, e):
        if not self.meat_vm:
            return
        asyncio.create_task(self.meat_vm.load_meat_types_command())

        meat_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=200)
        cat_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=150)
        new_mt_field = ft.TextField(label="Nouveau type de viande", width=200, dense=True)
        new_cat_field = ft.TextField(label="Nouvelle catégorie", width=200, dense=True)

        def _on_meat_vm_changed(prop):
            if prop == "meat_types":
                meat_list.controls.clear()
                for mt in self.meat_vm.meat_types:
                    selected = self.meat_vm.selected_meat_type and self.meat_vm.selected_meat_type.id == mt.id
                    meat_list.controls.append(
                        ft.Row([
                            ft.TextButton(mt.name, on_click=lambda ev, m=mt: asyncio.create_task(self.meat_vm.select_meat_type(m)),
                                          style=ft.ButtonStyle(bgcolor=ft.Colors.RED_100 if selected else None)),
                            ft.Container(expand=True),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=18,
                                          on_click=lambda ev, mid=str(mt.id), mn=mt.name: confirm_dialog(self.page, "Supprimer le type de viande", f"Supprimer '{mn}' ?", lambda: asyncio.create_task(self.meat_vm.delete_meat_type_command(mid)))),
                        ])
                    )
                self.page.update()
            elif prop == "categories":
                cat_list.controls.clear()
                if not self.meat_vm.categories:
                    cat_list.controls.append(ft.Text("Sélectionnez un type de viande pour voir les catégories", size=12, color=ft.Colors.GREY_600))
                for cat in self.meat_vm.categories:
                    cat_list.controls.append(
                        ft.Row([
                            ft.Text(cat.name, size=14),
                            ft.Container(expand=True),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=18,
                                          on_click=lambda ev, cid=str(cat.id), cn=cat.name: confirm_dialog(self.page, "Supprimer la catégorie", f"Supprimer '{cn}' ?", lambda: asyncio.create_task(self.meat_vm.delete_category_command(cid)))),
                        ])
                    )
                self.page.update()

        self.meat_vm.add_listener(_on_meat_vm_changed)

        async def _add_mt(ev):
            self.meat_vm.new_meat_type_name = new_mt_field.value or ""
            await self.meat_vm.create_meat_type_command()
            new_mt_field.value = ""
            self.page.update()

        async def _add_cat(ev):
            self.meat_vm.new_category_name = new_cat_field.value or ""
            await self.meat_vm.create_category_command()
            new_cat_field.value = ""
            self.page.update()

        def _close(ev):
            self.meat_vm.remove_listener(_on_meat_vm_changed)
            asyncio.create_task(self.vm.load_meat_types_command())
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Types de viande & Catégories"),
                content=ft.Column([
                    ft.Text("Types de viande", size=14, weight=ft.FontWeight.W_500),
                    ft.Row([new_mt_field, ft.Button("Ajouter", on_click=lambda ev: asyncio.create_task(_add_mt(ev)))]),
                    meat_list,
                    ft.Divider(),
                    ft.Text("Catégories", size=14, weight=ft.FontWeight.W_500),
                    ft.Row([new_cat_field, ft.Button("Ajouter", on_click=lambda ev: asyncio.create_task(_add_cat(ev)))]),
                    cat_list,
                ], spacing=8, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Terminé"), on_click=_close),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _open_edit_dialog(self, product):
        name_field = ft.TextField(
            label="Nom du produit", width=280, dense=True,
            value=product.name,
        )
        price_field = ft.TextField(
            label="Prix (DZD)", width=280, dense=True,
            keyboard_type=ft.KeyboardType.NUMBER, value=str(product.price),
        )
        unit_dropdown = ft.Dropdown(
            label="Unité", width=280, dense=True,
            options=[ft.dropdown.Option(UnitType.weight.value, "Poids (kg)"), ft.dropdown.Option(UnitType.unit.value, "Unité")],
            value=product.unit_type.value,
        )
        avail_switch = ft.Switch(label="Disponible", value=product.is_available)

        async def _save(ev):
            data = {}
            if name_field.value and name_field.value != product.name:
                data["name"] = name_field.value
            if price_field.value and float(price_field.value) != float(product.price):
                data["price"] = float(price_field.value)
            if unit_dropdown.value and unit_dropdown.value != product.unit_type.value:
                data["unit_type"] = unit_dropdown.value
            if avail_switch.value != product.is_available:
                data["is_available"] = avail_switch.value
            self.page.pop_dialog()
            if data:
                await self.vm.update_product_command(str(product.id), data)

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Modifier {product.name}"),
                content=ft.Column([
                    name_field,
                    price_field,
                    unit_dropdown,
                    avail_switch,
                ], spacing=12, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Annuler"), on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton(content=ft.Text("Enregistrer", color=ft.Colors.RED), on_click=lambda e: asyncio.create_task(_save(e))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _open_add_dialog(self, e):
        meat_type_dropdown = ft.Dropdown(
            label="Type de viande", width=280, dense=True,
            options=[ft.dropdown.Option(key=str(mt.id), text=mt.name) for mt in self.vm.meat_types],
        )
        category_dropdown = ft.Dropdown(label="Catégorie", width=280, dense=True, disabled=True)
        price_field = ft.TextField(label="Prix (DZD)", width=280, dense=True, keyboard_type=ft.KeyboardType.NUMBER)
        unit_dropdown = ft.Dropdown(
            label="Unité", width=280, dense=True,
            options=[ft.dropdown.Option(UnitType.weight.value, "Poids (kg)"), ft.dropdown.Option(UnitType.unit.value, "Unité")],
            value=UnitType.weight.value,
        )

        def _update_name():
            mt_name = ""
            for mt in self.vm.meat_types:
                if str(mt.id) == meat_type_dropdown.value:
                    mt_name = mt.name
                    break
            cat_name = ""
            for cat in self.vm.categories:
                if str(cat.id) == category_dropdown.value:
                    cat_name = cat.name
                    break
            if mt_name and cat_name:
                self.vm.new_name = f"{mt_name} {cat_name}"

        def _on_meat_select(ev):
            category_dropdown.disabled = False
            category_dropdown.value = None
            self.vm.new_name = ""
            meat_type_id = ev.control.value
            if meat_type_id:
                asyncio.create_task(self.vm._load_categories_by_meat(meat_type_id))
                category_dropdown.options = []
            self.page.update()

        def _on_category_select(ev):
            _update_name()
            self.page.update()

        meat_type_dropdown.on_select = _on_meat_select
        category_dropdown.on_select = _on_category_select

        def _on_vm_changed_dialog(prop: str):
            if prop == "categories":
                category_dropdown.options = [
                    ft.dropdown.Option(key=str(cat.id), text=cat.name)
                    for cat in self.vm.categories
                ]
                self.page.update()

        self.vm.add_listener(_on_vm_changed_dialog)

        async def _submit(ev):
            self.vm.new_price = price_field.value or ""
            self.vm.new_unit_type = UnitType(unit_dropdown.value)
            self.vm.selected_category_id = category_dropdown.value
            self.vm.remove_listener(_on_vm_changed_dialog)
            self.page.pop_dialog()
            await self.vm.create_product_command()
            self.page.update()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Ajouter un produit"),
                content=ft.Column([
                    meat_type_dropdown,
                    category_dropdown,
                    price_field,
                    unit_dropdown,
                ], spacing=12, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Annuler"), on_click=lambda e: (self.vm.remove_listener(_on_vm_changed_dialog), self.page.pop_dialog())),
                    ft.TextButton(content=ft.Text("Ajouter", color=ft.Colors.RED), on_click=lambda e: asyncio.create_task(_submit(e))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    async def _toggle_avail(self, product):
        await self.vm.toggle_availability_command(product)

    async def _delete(self, product_id: str):
        await self.vm.delete_product_command(product_id)

    def render(self) -> ft.Control:
        return self.content
