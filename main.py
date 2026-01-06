import flet as ft
from components.sidebar import Sidebar
from views.content_views import Views
from assets.colors import BG_PAGE

def main(page: ft.Page):
    page.window.width = 800
    page.window.height = 720
    page.bgcolor = BG_PAGE
    page.padding = 0

    # Initialize the content area with the MainView object
    content_area = ft.Container(
        expand=True, 
        content=Views.get_view("Main"), 
        alignment=ft.Alignment(0, 0)
    )

    def route_change(name):
        # name will be "Main", "Form", or "Settings"
        content_area.content = Views.get_view(name)
        page.update()

    sidebar = Sidebar(on_route_change=route_change)

    page.add(
        ft.Column(
            expand=True,
            controls=[
                ft.WindowDragArea(height=50, content=ft.Container()), 
                ft.Row(
                    expand=True,
                    controls=[
                        ft.Container(content=sidebar, padding=10), 
                        content_area 
                    ]
                )
            ]
        )
    )

if __name__ == '__main__':
    ft.run(main)