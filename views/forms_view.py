import flet as ft
import json

class FormsView(ft.Column):
    def __init__(self):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 0
        self.padding = 20
        
        # CSV file state
        self.csv_file_path = None
        self.csv_file_name = ft.Text("No file selected", color="#666666", size=12)
        
        # JSON file state
        self.json_file_path = None
        self.json_file_name = ft.Text("No file selected", color="#666666", size=12)
        
        # JSON editor
        self.json_editor = ft.TextField(
            label="JSON Editor",
            multiline=True,
            min_lines=20,
            max_lines=25,
            value="",
            border_color="#d0d0d0",
            focused_border_color="#1f2525",
            text_style=ft.TextStyle(font_family="Courier New", size=11),
        )
        
        # Form container with two columns
        self.form_container = ft.Row(
            expand=True,
            spacing=20,
            controls=[
                # Left column - File inputs
                ft.Column(
                    width=350,
                    spacing=15,
                    controls=[
                        ft.Text("Form Creations", size=30, weight="bold", color="#1f2525"),
                        ft.Divider(height=1, color="#e0e0e0"),
                        
                        # CSV Section
                        ft.Container(
                            padding=15,
                            bgcolor="#f5f5f5",
                            border_radius=8,
                            content=ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Text("CSV File", size=14, weight="bold", color="#1f2525"),
                                    ft.Button(
                                        content="Choose CSV",
                                        icon=ft.Icons.INSERT_DRIVE_FILE,
                                        on_click=self.handle_csv_pick,
                                        width=320,
                                    ),
                                    self.csv_file_name,
                                ]
                            ),
                        ),
                        
                        # JSON Section
                        ft.Container(
                            padding=15,
                            bgcolor="#f5f5f5",
                            border_radius=8,
                            content=ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Text("JSON File", size=14, weight="bold", color="#1f2525"),
                                    ft.Button(
                                        content="Choose JSON",
                                        icon=ft.Icons.DATA_OBJECT,
                                        on_click=self.handle_json_pick,
                                        width=320,
                                    ),
                                    self.json_file_name,
                                ]
                            ),
                        ),
                        
                        # Action buttons
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Button(
                                    content="Save JSON",
                                    icon=ft.Icons.SAVE,
                                    on_click=self.handle_save_json,
                                    width=160,
                                ),
                                ft.Button(
                                    content="Reset",
                                    icon=ft.Icons.REFRESH,
                                    on_click=self.handle_reset,
                                    width=160,
                                ),
                            ]
                        ),
                    ]
                ),
                
                # Right column - JSON Editor
                ft.Column(
                    expand=True,
                    spacing=10,
                    controls=[
                        ft.Text("Editor", size=14, weight="bold", color="#1f2525"),
                        ft.Container(
                            expand=True,
                            padding=10,
                            bgcolor="white",
                            border=ft.border.all(1, "#d0d0d0"),
                            border_radius=8,
                            content=self.json_editor,
                        ),
                    ]
                ),
            ]
        )
        
        self.controls = [self.form_container]
    
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
            
            # Load and display JSON in editor
            try:
                with open(files[0].path, 'r') as f:
                    json_data = json.load(f)
                    self.json_editor.value = json.dumps(json_data, indent=2)
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
            # Validate JSON
            json_data = json.loads(self.json_editor.value)
            
            # Save to file
            with open(self.json_file_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            self.json_editor.error_text = None
            self.json_editor.label = "✓ Saved successfully!"
            self.json_editor.update()
        except json.JSONDecodeError as ex:
            self.json_editor.error_text = f"Invalid JSON: {str(ex)}"
            self.json_editor.update()
        except Exception as ex:
            self.json_editor.error_text = f"Error: {str(ex)}"
            self.json_editor.update()
    
    async def handle_reset(self, e):
        self.csv_file_path = None
        self.json_file_path = None
        self.csv_file_name.value = "No file selected"
        self.csv_file_name.color = "#666666"
        self.json_file_name.value = "No file selected"
        self.json_file_name.color = "#666666"
        self.json_editor.value = ""
        self.json_editor.label = "JSON Editor"
        self.json_editor.error_text = None
        
        self.csv_file_name.update()
        self.json_file_name.update()
        self.json_editor.update()