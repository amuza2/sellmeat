import flet as ft
import asyncio

from viewmodels.manage_settings_viewmodel import ManageSettingsViewModel
from viewmodels.manage_slots_viewmodel import ManageSlotsViewModel
from components.ui import loading_indicator, error_with_retry, confirm_dialog, show_snackbar


class ManageSettingsView:
    def __init__(self, page: ft.Page, vm: ManageSettingsViewModel, on_back, session=None, on_logout=None, slots_vm: ManageSlotsViewModel = None):
        self.page = page
        self.vm = vm
        self.on_back = on_back
        self.session = session
        self.on_logout = on_logout
        self.slots_vm = slots_vm
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.settings_list = ft.Column(spacing=8)

        self.content = ft.Container(
            padding=20,
            expand=True,
            content=ft.Column(
            [
                ft.Text("Paramètres", size=24, weight=ft.FontWeight.BOLD),
                self.loading_ctrl,
                self.error_ctrl,
                self.settings_list,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ))

    def _on_vm_changed(self, prop: str):
        if prop == "delivery_fee":
            self._render_settings()
        elif prop == "error":
            self.error_ctrl.content = error_with_retry(self.vm.error, self._retry) if self.vm.error else None
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_indicator() if self.vm.is_loading else None
        elif prop == "is_saved":
            if self.vm.is_saved:
                show_snackbar(self.page, "Paramètres enregistrés !")
                self.vm.is_saved = False
                self._render_settings()
        self.page.update()

    def _retry(self, e=None):
        asyncio.create_task(self.vm.load_command())

    def _render_settings(self):
        self.settings_list.controls.clear()

        is_seller = self.session and self.session.is_seller

        if is_seller:
            fee_display = f"{self.vm.delivery_fee} DZD" if self.vm.delivery_fee else "Non défini"
            self.settings_list.controls.append(
                self._settings_item(
                    icon=ft.Icons.LOCAL_SHIPPING,
                    title="Frais de livraison",
                    subtitle=fee_display,
                    on_click=self._open_fee_dialog,
                )
            )

        if self.session and self.session.user:
            self.settings_list.controls.append(
                self._settings_item(
                    icon=ft.Icons.PERSON,
                    title="Compte",
                    subtitle=f"{self.session.user.name} ({self.session.user.role.value})",
                    on_click=None,
                )
            )

        if self.slots_vm:
            active_count = sum(1 for s in self.slots_vm.slots if s.is_active) if self.slots_vm.slots else 0
            total_count = len(self.slots_vm.slots) if self.slots_vm.slots else 0
            self.settings_list.controls.append(
                self._settings_item(
                    icon=ft.Icons.SCHEDULE,
                    title="Créneaux de livraison",
                    subtitle=f"{active_count} actifs / {total_count} total",
                    on_click=self._open_slots_dialog,
                )
            )

        self.settings_list.controls.append(
            self._settings_item(
                icon=ft.Icons.LOGOUT,
                title="Déconnexion",
                subtitle="Se déconnecter de votre compte",
                on_click=self._on_logout_click,
                icon_color=ft.Colors.RED,
            )
        )

    def _settings_item(self, icon, title, subtitle, on_click, icon_color=None):
        return ft.Card(
            content=ft.Container(
                padding=14,
                on_click=on_click,
                ink=True,
                content=ft.Row([
                    ft.Icon(icon, color=icon_color or ft.Colors.RED_700, size=24),
                    ft.Column([
                        ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400, size=20),
                ]),
            ),
        )

    def _open_fee_dialog(self, e):
        fee_field = ft.TextField(
            label="Frais de livraison (DZD)", width=280, dense=True,
            keyboard_type=ft.KeyboardType.NUMBER, value=self.vm.delivery_fee,
        )

        async def _save(ev):
            self.vm.delivery_fee = fee_field.value or "0"
            self.page.pop_dialog()
            await self.vm.save_command()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Frais de livraison"),
                content=ft.Column([
                    ft.Text("Ces frais seront appliqués à toutes les nouvelles commandes.", size=12, color=ft.Colors.GREY_600),
                    fee_field,
                ], spacing=12, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Annuler"), on_click=lambda e: self.page.pop_dialog()),
                    ft.TextButton(content=ft.Text("Enregistrer", color=ft.Colors.RED), on_click=lambda e: asyncio.create_task(_save(e))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _open_slots_dialog(self, e):
        if not self.slots_vm:
            return
        asyncio.create_task(self.slots_vm.load_command())

        slots_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=300)
        label_field = ft.TextField(label="Libellé (ex. Matin)", dense=True, expand=True)
        time_field = ft.TextField(label="Heure (HH:MM)", dense=True, value="09:00", expand=True)

        def _on_slots_vm_changed(prop):
            if prop == "slots":
                slots_list.controls.clear()
                if not self.slots_vm.slots:
                    slots_list.controls.append(ft.Text("Aucun créneau de livraison", size=12, color=ft.Colors.GREY_600))
                for slot in self.slots_vm.slots:
                    slots_list.controls.append(
                        ft.Card(content=ft.Container(padding=6, content=ft.Column([
                            ft.Row([
                                ft.Text(slot.label, size=14, weight=ft.FontWeight.W_500),
                                ft.Container(expand=True),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED, icon_size=16,
                                              on_click=lambda ev, sid=str(slot.id), sl=slot.label: confirm_dialog(self.page, "Supprimer le créneau", f"Supprimer '{sl}' ?", lambda: asyncio.create_task(self.slots_vm.delete_command(sid)))),
                            ]),
                            ft.Text(f"Livraison à {slot.delivery_time.strftime('%H:%M')}", size=12, color=ft.Colors.GREY_600),
                            ft.Switch(
                                label="Actif", value=slot.is_active,
                                on_change=lambda ev, s=slot: asyncio.create_task(self.slots_vm.toggle_active_command(s)),
                            ),
                        ], spacing=2)))
                    )
                self.page.update()

        self.slots_vm.add_listener(_on_slots_vm_changed)

        async def _add_slot(ev):
            self.slots_vm.new_label = label_field.value or ""
            self.slots_vm.new_time = time_field.value or "09:00"
            await self.slots_vm.create_command()
            label_field.value = ""
            self.page.update()

        def _close(ev):
            self.slots_vm.remove_listener(_on_slots_vm_changed)
            self._render_settings()
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Créneaux de livraison"),
                content=ft.Column([
                    label_field,
                    time_field,
                    ft.Button("Ajouter un créneau", on_click=lambda ev: asyncio.create_task(_add_slot(ev)), width=300),
                    ft.Divider(),
                    slots_list,
                ], spacing=10, tight=True),
                actions=[
                    ft.TextButton(content=ft.Text("Terminé"), on_click=_close),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _on_logout_click(self, e):
        confirm_dialog(self.page, "Déconnexion", "Êtes-vous sûr de vouloir vous déconnecter ?", self._do_logout, confirm_label="Déconnexion")

    def _do_logout(self):
        if self.session:
            self.session.logout()
        if self.on_logout:
            self.on_logout()

    def render(self) -> ft.Control:
        self._render_settings()
        return self.content
