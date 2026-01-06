import flet as ft
from assets.colors import BG_ACTIVE, BG_HOVER, ICON_COLOR

class NavItem(ft.Container):
    def __init__(self, icon_data, text, name, on_click_callback, is_active=False):
        super().__init__()
        self.name = name
        self.is_active = is_active
        self.on_click_callback = on_click_callback
        
        self.content = ft.Row([
            ft.Container(
                content=ft.Icon(icon_data, color=ICON_COLOR, size=25),
                width=40,
                alignment=ft.Alignment(0, 0)
            ),
            ft.Text(text, color=ICON_COLOR, weight="w500", size=16)
        ], wrap=False, spacing=10)

        # FIXED: Use ft.Padding (Capital P) to avoid DeprecationWarning
        self.padding = ft.Padding.symmetric(vertical=8, horizontal=0)
        
        self.border_radius = 10
        self.ink = True
        
        # Apply active state
        self.bgcolor = BG_ACTIVE if is_active else None
        self.shadow = ft.BoxShadow(blur_radius=10, color="black") if is_active else None
        
        # Bind events
        self.on_click = lambda _: self.on_click_callback(self.name)
        self.on_hover = self.handle_hover

    def handle_hover(self, e):
        if not self.is_active:
            self.bgcolor = BG_HOVER if e.data == "true" else None
            self.update()