"""Google Login View for authentication UI."""

import flet as ft
import asyncio
from services.google_auth import GoogleAuthService


class LoginView(ft.Column):
    """UI for Google OAuth2 authentication."""
    
    def __init__(self, on_auth_success=None, on_auth_error=None):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.padding = 40
        self.expand = True
        
        self.auth_service = GoogleAuthService()
        self.on_auth_success = on_auth_success
        self.on_auth_error = on_auth_error
        
        # Status indicator
        self.status_text = ft.Text(
            "Ready to authenticate",
            size=14,
            color="#666666",
            text_align=ft.TextAlign.CENTER
        )
        
        # Main container
        self.main_container = ft.Container(
            width=400,
            bgcolor="white",
            border_radius=12,
            padding=40,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color="#00000015",
                offset=ft.Offset(0, 2),
            ),
            content=ft.Column(
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Header
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(
                                ft.Icons.SECURITY,
                                size=48,
                                color="#4285F4"
                            ),
                            ft.Text(
                                "Google Authentication",
                                size=24,
                                weight="bold",
                                color="#1f2525"
                            ),
                            ft.Text(
                                "Sign in with your Google account",
                                size=12,
                                color="#999999"
                            ),
                        ]
                    ),
                    
                    ft.Divider(height=1, color="#e0e0e0"),
                    
                    # Instructions
                    ft.Container(
                        padding=15,
                        bgcolor="#f0f4ff",
                        border_radius=8,
                        border=ft.Border.all(1, "#d0dcff"),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    "Setup Instructions:",
                                    size=12,
                                    weight="bold",
                                    color="#1f2525"
                                ),
                                ft.Text(
                                    "1. Place your credentials.json in the data folder",
                                    size=11,
                                    color="#666666"
                                ),
                                ft.Text(
                                    "2. Click 'Login with Google' button",
                                    size=11,
                                    color="#666666"
                                ),
                                ft.Text(
                                    "3. Complete the authentication in your browser",
                                    size=11,
                                    color="#666666"
                                ),
                            ]
                        )
                    ),
                    
                    # Credentials status
                    self.get_credentials_status_container(),
                    
                    # Login button
                    ft.FilledButton(
                        content="Login with Google",
                        icon=ft.Icons.LOGIN,
                        width=300,
                        height=45,
                        style=ft.ButtonStyle(
                            bgcolor="#4285F4",
                            color="white",
                        ),
                        on_click=self.handle_login,
                    ),
                    
                    # Status message
                    self.status_text,
                ]
            ),
        )
        
        self.controls = [self.main_container]
    
    def get_credentials_status_container(self) -> ft.Container:
        """Create credentials status display."""
        credentials_exist = self.auth_service.credentials_file_exists()
        
        if credentials_exist:
            status_color = "#4CAF50"
            status_icon = ft.Icons.CHECK_CIRCLE
            status_msg = "✓ credentials.json found"
        else:
            status_color = "#FF6B6B"
            status_icon = ft.Icons.ERROR_OUTLINE
            status_msg = "✗ credentials.json not found"
        
        return ft.Container(
            padding=12,
            bgcolor=f"{status_color}15",
            border_radius=8,
            border=ft.Border.all(1, status_color),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(status_icon, color=status_color, size=20),
                    ft.Text(
                        status_msg,
                        color=status_color,
                        weight="500",
                        size=12
                    ),
                ]
            ),
        )
    
    async def handle_login(self, e):
        """Handle login button click."""
        self.status_text.value = "Checking credentials..."
        self.status_text.color = "#FFA500"
        self.status_text.update()
        
        # Check if credentials file exists
        if not self.auth_service.credentials_file_exists():
            self.status_text.value = "✗ credentials.json not found in ~/.quaestionarius/"
            self.status_text.color = "#FF6B6B"
            self.show_error_dialog(
                "Missing credentials.json",
                f"Please place your credentials.json file in:\n~/.quaestionarius/credentials.json"
            )
            if self.on_auth_error:
                self.on_auth_error("Credentials file not found")
            self.status_text.update()
            return
        
        # Try to load existing token
        if self.auth_service.token_file_exists():
            self.status_text.value = "Loading existing credentials..."
            self.status_text.color = "#FFA500"
            self.status_text.update()
            
            if self.auth_service.load_token_from_pickle():
                if self.auth_service.is_authenticated():
                    self.status_text.value = "✓ Successfully logged in!"
                    self.status_text.color = "#4CAF50"
                    self.status_text.update()
                    if self.on_auth_success:
                        self.on_auth_success()
                    return
        
        # Perform new authentication
        self.status_text.value = "Opening browser for authentication..."
        self.status_text.color = "#FFA500"
        self.status_text.update()
        
        try:
            success = self.auth_service.authenticate()
            if success:
                self.status_text.value = "✓ Successfully logged in!"
                self.status_text.color = "#4CAF50"
                if self.on_auth_success:
                    self.on_auth_success()
            else:
                self.status_text.value = "✗ Authentication failed"
                self.status_text.color = "#FF6B6B"
                if self.on_auth_error:
                    self.on_auth_error("Authentication failed")
        except Exception as ex:
            self.status_text.value = f"✗ Error: {str(ex)}"
            self.status_text.color = "#FF6B6B"
            self.show_error_dialog("Authentication Error", str(ex))
            if self.on_auth_error:
                self.on_auth_error(str(ex))
        
        self.status_text.update()
    
    def show_error_dialog(self, title: str, message: str):
        """Show error dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton(
                    text="Close",
                    on_click=lambda e: self._close_dialog(e, dialog)
                ),
            ],
        )
        # Note: This requires page context to show
        print(f"{title}: {message}")
    
    @staticmethod
    def _close_dialog(e, dialog):
        """Close alert dialog."""
        if hasattr(e, 'page'):
            e.page.dialog = None
            e.page.update()


class LoginStatusView(ft.Container):
    """Display user login status and logout option."""
    
    def __init__(self, auth_service: GoogleAuthService, on_logout=None):
        super().__init__()
        self.auth_service = auth_service
        self.on_logout = on_logout
        self.padding = 20
        self.bgcolor = "#f5f5f5"
        self.border_radius = 8
        
        self.status_column = ft.Column(spacing=15)
        self.content = self.status_column
        # Initialize controls without calling update() before attachment
        self._set_status_controls(self.auth_service.is_authenticated())

    def _set_status_controls(self, is_authed: bool):
        """Populate the status column based on auth state without updating page."""
        if is_authed:
            self.status_column.controls = [
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color="#4CAF50", size=24),
                                ft.Text(
                                    "Authenticated",
                                    size=18,
                                    weight="bold",
                                    color="#4CAF50"
                                ),
                            ]
                        ),
                        ft.Divider(height=1, color="#e0e0e0"),
                        ft.Text(
                            "Your Google account is connected",
                            size=12,
                            color="#666666"
                        ),
                        ft.Button(
                            text="Logout",
                            icon=ft.Icons.LOGOUT,
                            on_click=self.handle_logout,
                            width=200,
                            style=ft.ButtonStyle(
                                bgcolor="#FF6B6B",
                                color="white",
                            ),
                        ),
                    ]
                )
            ]
        else:
            self.status_column.controls = [
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.CANCEL, color="#FF6B6B", size=24),
                                ft.Text(
                                    "Not Authenticated",
                                    size=18,
                                    weight="bold",
                                    color="#FF6B6B"
                                ),
                            ]
                        ),
                        ft.Divider(height=1, color="#e0e0e0"),
                        ft.Text(
                            "Please login to continue",
                            size=12,
                            color="#666666"
                        ),
                    ]
                )
            ]
    
    def update_status(self):
        """Update the login status display."""
        self._set_status_controls(self.auth_service.is_authenticated())
        # Only call update when the control is attached to a page
        try:
            if self.page:
                self.update()
        except RuntimeError:
            # page property access can raise if not yet attached; ignore safely
            pass
    
    async def handle_logout(self, e):
        """Handle logout action."""
        self.auth_service.logout()
        self.update_status()
        if self.on_logout:
            self.on_logout()
