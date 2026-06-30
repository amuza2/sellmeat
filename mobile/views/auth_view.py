import flet as ft
import asyncio

from viewmodels.auth_viewmodel import AuthViewModel
from components.ui import error_text, loading_indicator


class AuthView:
    def __init__(self, page: ft.Page, vm: AuthViewModel, on_auth_success):
        self.page = page
        self.vm = vm
        self.on_auth_success = on_auth_success
        self.vm.add_listener(self._on_vm_changed)
        self._build()

    def _build(self):
        title = ft.Text("لحم طازج", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
        subtitle = ft.Text("Viande fraîche livrée chez vous", size=14, color=ft.Colors.GREY_600)

        self.email_field = ft.TextField(
            label="Email", value=self.vm.email, on_change=self._on_email_change,
            keyboard_type=ft.KeyboardType.EMAIL, width=320,
        )
        self.password_field = ft.TextField(
            label="Mot de passe", value=self.vm.password, on_change=self._on_password_change,
            password=True, can_reveal_password=True, width=320,
        )
        self.name_field = ft.TextField(
            label="Nom complet", value=self.vm.name, on_change=self._on_name_change, width=320,
        )
        self.phone_field = ft.TextField(
            label="Numéro de téléphone", value=self.vm.phone, on_change=self._on_phone_change,
            keyboard_type=ft.KeyboardType.PHONE, width=320,
        )
        self.seller_checkbox = ft.Checkbox(
            label="S'inscrire en tant que vendeur", value=self.vm.is_seller,
            on_change=self._on_seller_change,
        )

        self.mode_button = ft.TextButton(
            content=ft.Text("Pas de compte ? Inscrivez-vous" if self.vm.is_login_mode else "Déjà un compte ? Connectez-vous"),
            on_click=self._on_toggle_mode,
        )

        self.submit_button = ft.Button(
            "Connexion" if self.vm.is_login_mode else "S'inscrire",
            on_click=lambda e: asyncio.create_task(self._on_submit(e)), width=320, height=45,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
        )

        self.dev_buttons = ft.Row(
            [
                ft.OutlinedButton("Démo vendeur", on_click=lambda e: asyncio.create_task(self._quick_login("seller@sellmeat.com", "password123"))),
                ft.OutlinedButton("Démo client", on_click=lambda e: asyncio.create_task(self._quick_login("customer@example.com", "password123"))),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.error_ctrl = ft.Container()
        self.loading_ctrl = ft.Container()

        self.register_fields = ft.Column(
            [self.name_field, self.phone_field, self.seller_checkbox],
            visible=not self.vm.is_login_mode,
        )

        self.content = ft.Column(
            [
                title, subtitle,
                ft.Container(height=20),
                self.email_field,
                self.password_field,
                self.register_fields,
                self.error_ctrl,
                self.loading_ctrl,
                self.submit_button,
                self.mode_button,
                ft.Container(height=10),
                ft.Text("Connexion démo rapide", size=11, color=ft.Colors.GREY_500),
                self.dev_buttons,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

    def _on_email_change(self, e):
        self.vm.email = e.control.value

    def _on_password_change(self, e):
        self.vm.password = e.control.value

    def _on_name_change(self, e):
        self.vm.name = e.control.value

    def _on_phone_change(self, e):
        self.vm.phone = e.control.value

    def _on_seller_change(self, e):
        self.vm.is_seller = e.control.value
        self.phone_field.visible = not e.control.value
        self.page.update()

    def _on_toggle_mode(self, e):
        self.vm.toggle_mode_command()
        self.submit_button.text = "Connexion" if self.vm.is_login_mode else "S'inscrire"
        self.register_fields.visible = not self.vm.is_login_mode
        self.mode_button.content = ft.Text("Pas de compte ? Inscrivez-vous" if self.vm.is_login_mode else "Déjà un compte ? Connectez-vous")
        self.page.update()

    async def _on_submit(self, e):
        if self.vm.is_login_mode:
            await self.vm.login_command()
        else:
            await self.vm.register_command()
        if self.vm.is_loading == False and self.vm.error == "" and self.vm.session.is_authenticated:
            self.on_auth_success()

    async def _quick_login(self, email: str, password: str):
        self.vm.email = email
        self.vm.password = password
        self.email_field.value = email
        self.password_field.value = password
        self.page.update()
        await self.vm.login_command()
        if self.vm.is_loading == False and self.vm.error == "" and self.vm.session.is_authenticated:
            self.on_auth_success()

    def _on_vm_changed(self, prop: str):
        if prop == "error":
            self.error_ctrl.content = error_text(self.vm.error) if self.vm.error else None
            self.page.update()
        elif prop == "is_loading":
            self.loading_ctrl.content = loading_indicator() if self.vm.is_loading else None
            self.submit_button.disabled = self.vm.is_loading
            self.page.update()

    def render(self) -> ft.Control:
        return ft.Container(
            content=self.content,
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=30,
        )
