import flet as ft
import time
from .nav_item import NavItem
from assets.colors import BG_SIDEBAR, DIVIDER_COLOR

class Sidebar(ft.Container):
    def __init__(self, on_route_change):
        super().__init__()
        self.on_route_change = on_route_change
        self.active_view_name = "Main"
        
        # FIXED: Re-assigned the menu button container logic correctly
        self.menu_btn = ft.Container(
            content=ft.Icon(ft.Icons.MENU, color="white", size=20),
            width=30, height=30, bgcolor='#545c5b', border_radius=8,
            on_click=self.animate_sidebar
        )
        
        self.divider = ft.Container(
            width=40, height=1, bgcolor=DIVIDER_COLOR, 
            animate=ft.Animation(400, "linear")
        )

        self.nav_items_col = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.START, 
            spacing=10,
            expand=True 
        )

        self.width = 60
        self.height = 480
        # FIXED: Using uppercase Padding for modern Flet versions
        self.padding = ft.Padding(10, 10, 10, 10) 
        self.border_radius = 16
        self.animate = ft.Animation(duration=400, curve=ft.AnimationCurve.LINEAR)
        self.bgcolor = BG_SIDEBAR
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.content = self.nav_items_col
        
        self.render_items()

    def animate_sidebar(self, e):
        self.menu_btn.scale = 0.8
        self.update()
        time.sleep(0.05)
        self.menu_btn.scale = 1
        
        if self.width == 60:
            self.width = 200
            self.divider.width = 180
        else:
            self.width = 60
            self.divider.width = 40
        self.update()

    def render_items(self):
        top_items = [
            (ft.Icons.HOME, "Main", "Main"),
            (ft.Icons.ADD_CHART, "Form Creation", "Form"),
        ]
        
        bottom_items = [
            (ft.Icons.SETTINGS, "Settings", "Settings"),
        ]

        # 1. Start with the Menu button
        controls = [
            ft.Container(
                content=self.menu_btn, 
                alignment=ft.Alignment(0, 0), 
                width=40, 
                # FIXED: Using uppercase Margin to remove DeprecationWarning
                margin=ft.Margin.only(bottom=10) 
            )
        ]

        # 2. Add top navigation
        for icon, label, name in top_items:
            controls.append(NavItem(icon, label, name, self.handle_nav_click, name == self.active_view_name))

        # 3. Spacer
        controls.append(ft.Container(expand=True)) 

        # 4. Add bottom items
        controls.append(ft.Container(alignment=ft.Alignment(0, 0), content=self.divider, width=40))
        
        for icon, label, name in bottom_items:
            controls.append(NavItem(icon, label, name, self.handle_nav_click, name == self.active_view_name))

        self.nav_items_col.controls = controls

    def handle_nav_click(self, name):
        self.active_view_name = name
        self.render_items()
        self.on_route_change(name)
        if self.page:
            self.update()