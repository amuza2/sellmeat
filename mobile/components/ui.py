import flet as ft


def confirm_dialog(page: ft.Page, title: str, message: str, on_confirm, confirm_label: str = "Supprimer"):
    def _on_yes(e):
        page.pop_dialog()
        on_confirm()

    def _on_no(e):
        page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton(content=ft.Text("Annuler"), on_click=_on_no),
                ft.TextButton(content=ft.Text(confirm_label, color=ft.Colors.RED), on_click=_on_yes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )


def status_badge(status: str) -> ft.Container:
    labels = {
        "pending": "EN ATTENTE",
        "preparation": "PRÉPARATION",
        "delivering": "EN LIVRAISON",
        "delivered": "LIVRÉ",
        "cancelled": "ANNULÉ",
    }
    colors = {
        "pending": ft.Colors.ORANGE,
        "preparation": ft.Colors.BLUE,
        "delivering": ft.Colors.PURPLE,
        "delivered": ft.Colors.GREEN,
        "cancelled": ft.Colors.RED,
    }
    color = colors.get(status, ft.Colors.GREY)
    label = labels.get(status, status.upper())
    return ft.Container(
        content=ft.Text(label, size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )


def payment_badge(payment_status: str) -> ft.Container:
    color = ft.Colors.GREEN if payment_status == "paid" else ft.Colors.RED
    label = "PAYÉ" if payment_status == "paid" else "NON PAYÉ"
    return ft.Container(
        content=ft.Text(label, size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )


def loading_indicator() -> ft.ProgressRing:
    return ft.ProgressRing(width=24, height=24, stroke_width=3)


def error_text(message: str) -> ft.Text:
    return ft.Text(message, color=ft.Colors.RED, size=13)


def error_with_retry(message: str, on_retry) -> ft.Column:
    return ft.Column(
        [
            ft.Icon(ft.Icons.ERROR_OUTLINE, size=36, color=ft.Colors.RED_400),
            ft.Text(message, color=ft.Colors.RED, size=13, text_align=ft.TextAlign.CENTER),
            ft.OutlinedButton("Réessayer", icon=ft.Icons.REFRESH, on_click=on_retry),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )


def skeleton_card() -> ft.Card:
    bar = lambda w, h: ft.Container(
        width=w, height=h, bgcolor=ft.Colors.GREY_300, border_radius=6,
    )
    return ft.Card(
        content=ft.Container(
            padding=12,
            content=ft.Column([
                ft.Row([bar(160, 16), ft.Container(expand=True), bar(50, 16)]),
                ft.Row([bar(100, 12), ft.Container(expand=True), bar(60, 12)]),
            ], spacing=8),
        ),
    )


def loading_skeletons(count: int = 4) -> ft.Column:
    return ft.Column([skeleton_card() for _ in range(count)], spacing=8)


def empty_state(message: str) -> ft.Column:
    return ft.Column(
        [ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=ft.Colors.GREY_400),
         ft.Text(message, color=ft.Colors.GREY_500, size=14, text_align=ft.TextAlign.CENTER)],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def price_text(price, unit_type: str = "weight") -> ft.Text:
    suffix = "/kg" if unit_type == "weight" else "/unité"
    return ft.Text(f"{price:.2f} DZD{suffix}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)


def show_snackbar(page: ft.Page, message: str, duration: int = 2000):
    snack = ft.SnackBar(ft.Text(message), duration=duration)
    snack.open = True
    page.overlay.append(snack)
    page.update()
