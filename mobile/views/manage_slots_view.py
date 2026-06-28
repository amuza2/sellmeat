import flet as ft
import asyncio

from viewmodels.manage_slots_viewmodel import ManageSlotsViewModel
from components.ui import loading_indicator, empty_state, error_text, confirm_dialog


class ManageSlotsView:
    def __init__(self, page: ft.Page, vm: ManageSlotsViewModel, on_back):
        self.page = page
        self.vm = vm
        self.on_back = on_back
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.slots_list = ft.Column(spacing=8)
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.label_field = ft.TextField(label="Libellé (ex. Matin)", width=200, dense=True)
        self.time_field = ft.TextField(label="Heure (HH:MM)", width=120, dense=True, value="09:00")

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                    ft.Text("Créneaux de livraison", size=22, weight=ft.FontWeight.BOLD),
                ]),
                self.loading_ctrl,
                self.error_ctrl,
                ft.Text("Ajouter un créneau", size=16, weight=ft.FontWeight.W_500),
                ft.Column([
                    ft.Row([self.label_field, self.time_field], spacing=10),
                    ft.Button("Ajouter", on_click=lambda e: asyncio.create_task(self._on_add(e)), width=200),
                ], spacing=8),
                ft.Divider(),
                self.slots_list,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "slots":
            self._render_slots()
        elif prop == "error":
            self.error_ctrl.content = error_text(self.vm.error) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_indicator() if self.vm.is_loading else None
        self.page.update()

    def _render_slots(self):
        self.slots_list.controls.clear()
        if not self.vm.slots:
            self.slots_list.controls.append(empty_state("Aucun créneau de livraison"))
            return
        for slot in self.vm.slots:
            self.slots_list.controls.append(
                ft.Card(content=ft.Container(padding=12, content=ft.Column([
                    ft.Row([
                        ft.Text(slot.label, size=15, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=20,
                                      on_click=lambda e, sid=str(slot.id), sl=slot.label: confirm_dialog(self.page, "Supprimer le créneau", f"Supprimer '{sl}' ?", lambda: asyncio.create_task(self._delete(sid)))),
                    ]),
                    ft.Row([
                        ft.Text(f"Livraison à {slot.delivery_time.strftime('%H:%M')}", size=12, color=ft.Colors.GREY_600),
                        ft.Container(expand=True),
                        ft.Switch(
                            label="Actif", value=slot.is_active,
                            on_change=lambda e, s=slot: asyncio.create_task(self._toggle(s)),
                        ),
                    ]),
                ], spacing=4)))
            )

    async def _on_add(self, e):
        self.vm.new_label = self.label_field.value or ""
        self.vm.new_time = self.time_field.value or "09:00"
        await self.vm.create_command()
        self.label_field.value = ""
        self.page.update()

    async def _toggle(self, slot):
        await self.vm.toggle_active_command(slot)

    async def _delete(self, slot_id: str):
        await self.vm.delete_command(slot_id)

    def render(self) -> ft.Control:
        return self.content
