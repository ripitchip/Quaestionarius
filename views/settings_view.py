import flet as ft
import json
from views.login_view import LoginView, LoginStatusView
from services.google_auth import GoogleAuthService


class SettingsView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()

        self.page_ref = page
        self.expand = True
        self.spacing = 0
        self.padding = ft.padding.all(24)
        self.alignment = ft.MainAxisAlignment.START

        # Auth service
        self.auth_service = GoogleAuthService()

        self.login_status_view = LoginStatusView(
            self.auth_service,
            on_logout=self.on_logout_success
        )

        # File states
        self.credentials_file_path = None
        self.credentials_file_name = ft.Text("No file selected", size=12, color="#777")

        self.csv_file_path = None
        self.csv_file_name = ft.Text("No file selected", size=12, color="#777")

        self.json_file_path = None
        self.json_file_name = ft.Text("No file selected", size=12, color="#777")

        # JSON editor
        self.json_editor = ft.TextField(
            label="JSON Editor",
            multiline=True,
            min_lines=18,
            max_lines=25,
            border_radius=8,
            text_style=ft.TextStyle(
                font_family="Courier New",
                size=11
            ),
        )

        # Main layout
        self.controls = [
            ft.Text(
                "Settings",
                size=28,
                weight=ft.FontWeight.BOLD,
                color="#1f2525"
            ),
            ft.Text(
                "Configure authentication and application files",
                size=13,
                color="#666",
            ),
            ft.Container(height=20),

            ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=24,
                controls=[
                    self._google_auth_card(),
                ],
            )
        ]

    # ---------- UI BUILDERS ----------

    def _section_header(self, icon, title, subtitle=None):
        return ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(icon, size=22, color="#4285F4"),
                        ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Text(subtitle, size=12, color="#777") if subtitle else ft.Container(),
            ],
        )

    def _card(self, content):
        return ft.Container(
            padding=20,
            bgcolor="#ffffff",
            border_radius=12,
            border=ft.Border.all(1, "#e0e0e0"),
            content=content,
        )

    def _google_auth_card(self):
        return self._card(
            ft.Column(
                spacing=20,
                controls=[
                    self._section_header(
                        ft.Icons.SECURITY,
                        "Google Authentication",
                        "Connect your Google account securely"
                    ),
                    ft.Divider(),

                    # Credentials upload
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(
                                "Step 1: Upload credentials.json",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Download this file from Google Cloud Console",
                                size=12,
                                color="#666",
                            ),
                            ft.ElevatedButton(
                                "Choose credentials.json",
                                icon=ft.Icons.UPLOAD_FILE,
                                width=260,
                                on_click=self.handle_credentials_pick,
                            ),
                            self.credentials_file_name,
                        ],
                    ),

                    ft.Divider(),

                    # Login
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text(
                                "Step 2: Authenticate",
                                weight=ft.FontWeight.BOLD,
                            ),
                            self.login_status_view,
                            LoginView(
                                on_auth_success=self.on_auth_success,
                                on_auth_error=self.on_auth_error,
                            ),
                        ],
                    ),
                ],
            )
        )

    # ---------- HANDLERS (UNCHANGED) ----------

    async def handle_csv_pick(self, e):
        files = await ft.FilePicker().pick_files(
            allowed_extensions=["csv"],
            dialog_title="Pick a CSV file"
        )
        if files:
            self.csv_file_path = files[0].path
            self.csv_file_name.value = f"✓ {files[0].name}"
            self.csv_file_name.color = "#4CAF50"
            self.csv_file_name.update()

    async def handle_json_pick(self, e):
        files = await ft.FilePicker().pick_files(
            allowed_extensions=["json"],
            dialog_title="Pick a JSON file"
        )
        if files:
            self.json_file_path = files[0].path
            self.json_file_name.value = f"✓ {files[0].name}"
            self.json_file_name.color = "#4CAF50"

            try:
                with open(files[0].path, "r") as f:
                    self.json_editor.value = json.dumps(json.load(f), indent=2)
            except Exception as ex:
                self.json_editor.value = f"Error loading JSON: {str(ex)}"

            self.json_file_name.update()
            self.json_editor.update()

    async def handle_save_json(self, e):
        if not self.json_file_path:
            self.json_editor.error_text = "No JSON file selected"
            self.json_editor.update()
            return

        try:
            json_data = json.loads(self.json_editor.value)
            with open(self.json_file_path, "w") as f:
                json.dump(json_data, f, indent=2)

            self.json_editor.error_text = None
            self.json_editor.label = "✓ Saved successfully!"
        except json.JSONDecodeError as ex:
            self.json_editor.error_text = f"Invalid JSON: {str(ex)}"
        except Exception as ex:
            self.json_editor.error_text = f"Error: {str(ex)}"

        self.json_editor.update()

    async def handle_reset(self, e):
        self.csv_file_path = None
        self.json_file_path = None
        self.csv_file_name.value = "No file selected"
        self.json_file_name.value = "No file selected"
        self.json_editor.value = ""
        self.json_editor.error_text = None

        self.csv_file_name.update()
        self.json_file_name.update()
        self.json_editor.update()

    async def handle_credentials_pick(self, e):
        files = await ft.FilePicker().pick_files(
            allowed_extensions=["json"],
            dialog_title="Pick your credentials.json file"
        )
        if files:
            self.credentials_file_path = files[0].path
            self.credentials_file_name.value = f"✓ {files[0].name}"
            self.credentials_file_name.color = "#4CAF50"

            try:
                import shutil
                from pathlib import Path

                dest_dir = Path.home() / ".quaestionarius"
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(files[0].path, dest_dir / "credentials.json")

                self._snack("✓ credentials.json uploaded successfully!")
            except Exception as ex:
                self.credentials_file_name.value = f"✗ {str(ex)}"
                self.credentials_file_name.color = "#FF6B6B"
                self._snack(str(ex), error=True)

            self.credentials_file_name.update()

    # ---------- AUTH CALLBACKS ----------

    def on_auth_success(self):
        self.login_status_view.update_status()
        self._snack("Successfully authenticated with Google!")

    def on_auth_error(self, error_msg: str):
        self.login_status_view.update_status()
        self._snack(f"Authentication error: {error_msg}", error=True)

    def on_logout_success(self):
        self.login_status_view.update_status()
        self._snack("Successfully logged out")

    # ---------- UTIL ----------

    def _snack(self, text, error=False):
        if self.page_ref:
            self.page_ref.snack_bar = ft.SnackBar(
                ft.Text(text, color="white"),
                bgcolor="#FF6B6B" if error else None,
            )
            self.page_ref.snack_bar.open = True
            self.page_ref.update()
