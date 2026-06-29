import flet as ft
import asyncio
import logging

from viewmodels.manage_meat_viewmodel import ManageMeatViewModel
from components.ui import loading_indicator, empty_state, error_text, confirm_dialog

logger = logging.getLogger(__name__)


class ManageMeatView:
    def __init__(self, page: ft.Page, vm: ManageMeatViewModel, on_back):
        self.page = page
        self.vm = vm
        self.on_back = on_back
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.meat_type_list = ft.Column(spacing=6)
        self.category_list = ft.Column(spacing=6)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.new_mt_field = ft.TextField(label="Nouveau type de viande", dense=True, expand=True)
        self.new_cat_field = ft.TextField(label="Nouvelle catégorie", dense=True, expand=True)

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Types de viande & Catégories", size=22, weight=ft.FontWeight.BOLD),
                ]),
                self.loading_ctrl,
                self.error_ctrl,
                ft.Row([self.new_mt_field, ft.Button("Ajouter", on_click=lambda e: asyncio.create_task(self._on_add_mt(e)))]),
                self.meat_type_list,
                ft.Divider(),
                ft.Text("Catégories", size=16, weight=ft.FontWeight.W_500),
                ft.Row([self.new_cat_field, ft.Button("Ajouter", on_click=lambda e: asyncio.create_task(self._on_add_cat(e)))]),
                self.category_list,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "meat_types":
            self._render_meat_types()
        elif prop == "categories":
            self._render_categories()
        elif prop == "error":
            self.error_ctrl.content = error_text(self.vm.error) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_indicator() if self.vm.is_loading else None
        self.page.update()

    def _render_meat_types(self):
        self.meat_type_list.controls.clear()
        if not self.vm.meat_types:
            self.meat_type_list.controls.append(empty_state("Aucun type de viande"))
            return
        for mt in self.vm.meat_types:
            selected = self.vm.selected_meat_type and self.vm.selected_meat_type.id == mt.id
            self.meat_type_list.controls.append(
                ft.Row([
                    ft.TextButton(mt.name, on_click=lambda e, m=mt: asyncio.create_task(self._select_mt(m)),
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.RED_100 if selected else None)),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.EDIT_OUTLINE, icon_size=18,
                                  on_click=lambda e, mid=str(mt.id), mn=mt.name: self._edit_mt(mid, mn)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=18,
                                  on_click=lambda e, mid=str(mt.id), mn=mt.name: confirm_dialog(self.page, "Supprimer le type de viande", f"Supprimer '{mn}' ?", lambda: asyncio.create_task(self._delete_mt(mid)))),
                ])
            )

    def _render_categories(self):
        self.category_list.controls.clear()
        if not self.vm.categories:
            self.category_list.controls.append(empty_state("Sélectionnez un type de viande pour voir les catégories"))
            return
        for cat in self.vm.categories:
            self.category_list.controls.append(
                ft.Row([
                    ft.Text(cat.name, size=14),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.EDIT_OUTLINE, icon_size=18,
                                  on_click=lambda e, cid=str(cat.id), cn=cat.name: self._edit_cat(cid, cn)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=18,
                                  on_click=lambda e, cid=str(cat.id), cn=cat.name: confirm_dialog(self.page, "Supprimer la catégorie", f"Supprimer '{cn}' ?", lambda: asyncio.create_task(self._delete_cat(cid)))),
                ])
            )

    async def _on_add_mt(self, e):
        self.vm.new_meat_type_name = self.new_mt_field.value or ""
        if not self.vm.new_meat_type_name:
            self.page.snack_bar = ft.SnackBar(ft.Text("Veuillez saisir un nom"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()
            return
        await self.vm.create_meat_type_command()
        if not self.vm.error:
            self.new_mt_field.value = ""
            self.page.snack_bar = ft.SnackBar(ft.Text("Type de viande ajouté"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
        self.page.update()

    async def _on_add_cat(self, e):
        self.vm.new_category_name = self.new_cat_field.value or ""
        if not self.vm.new_category_name:
            self.page.snack_bar = ft.SnackBar(ft.Text("Veuillez saisir un nom"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()
            return
        if not self.vm.selected_meat_type:
            self.page.snack_bar = ft.SnackBar(ft.Text("Sélectionnez d'abord un type de viande"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()
            return
        await self.vm.create_category_command()
        if not self.vm.error:
            self.new_cat_field.value = ""
            self.page.snack_bar = ft.SnackBar(ft.Text("Catégorie ajoutée"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
        self.page.update()

    async def _select_mt(self, meat_type):
        await self.vm.select_meat_type(meat_type)

    def _edit_mt(self, meat_type_id: str, current_name: str):
        name_field = ft.TextField(label="Nom", value=current_name, autofocus=True)

        def do_edit(e):
            self.page.pop_dialog()
            new_name = name_field.value or ""
            if new_name and new_name != current_name:
                asyncio.create_task(self._do_edit_mt(meat_type_id, new_name))

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Modifier le type de viande"),
                content=ft.Column([name_field], tight=True),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton("Enregistrer", on_click=do_edit),
                ],
            )
        )

    def _edit_cat(self, category_id: str, current_name: str):
        name_field = ft.TextField(label="Nom", value=current_name, autofocus=True)

        def do_edit(e):
            self.page.pop_dialog()
            new_name = name_field.value or ""
            if new_name and new_name != current_name:
                asyncio.create_task(self._do_edit_cat(category_id, new_name))

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Modifier la catégorie"),
                content=ft.Column([name_field], tight=True),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton("Enregistrer", on_click=do_edit),
                ],
            )
        )

    async def _do_edit_mt(self, meat_type_id: str, new_name: str):
        await self.vm.update_meat_type_command(meat_type_id, new_name)
        if not self.vm.error:
            self.page.snack_bar = ft.SnackBar(ft.Text("Type de viande modifié"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

    async def _do_edit_cat(self, category_id: str, new_name: str):
        await self.vm.update_category_command(category_id, new_name)
        if not self.vm.error:
            self.page.snack_bar = ft.SnackBar(ft.Text("Catégorie modifiée"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

    async def _delete_mt(self, meat_type_id: str):
        logger.info(f"_delete_mt called: {meat_type_id}")
        await self.vm.delete_meat_type_command(meat_type_id)
        logger.info(f"_delete_mt done, error={self.vm.error}")
        if not self.vm.error:
            self.page.snack_bar = ft.SnackBar(ft.Text("Type de viande supprimé"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

    async def _delete_cat(self, category_id: str):
        logger.info(f"_delete_cat called: {category_id}")
        await self.vm.delete_category_command(category_id)
        logger.info(f"_delete_cat done, error={self.vm.error}")
        if not self.vm.error:
            self.page.snack_bar = ft.SnackBar(ft.Text("Catégorie supprimée"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

    def render(self) -> ft.Control:
        return self.content
