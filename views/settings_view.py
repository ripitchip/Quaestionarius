import flet as ft
file_picker = ft.FilePicker()

class SettingsView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True  # Makes it behave like a full subpage
        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text("Settings", size=30, weight="bold", color="#1f2525")
            ]
        )