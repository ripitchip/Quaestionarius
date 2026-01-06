import flet as ft

class MainView(ft.Column):
    def __init__(self):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.CENTER
        self.controls = [
            ft.Text("Main Page", size=30, weight="bold", color="#1f2525")
        ]