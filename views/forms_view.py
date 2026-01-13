import flet as ft
import csv

class FormsView(ft.Column):
    def __init__(self):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 0
        self.padding = 20
        
        # CSV file state
        self.csv_file_path = None
        self.csv_file_name = ft.Text("No file selected", color="#666666", size=12)
        
        # Team data
        self.teams_data = {}  # Dictionary: team_number -> list of members
        self.team_numbers = []  # Sorted list of team numbers
        self.current_team_index = 0
        
        # Team navigation text
        self.team_info_text = ft.Text("", size=16, weight="bold", color="#1f2525")
        
        # Navigation buttons
        self.prev_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self.handle_prev_team,
            disabled=True,
        )
        self.next_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self.handle_next_team,
            disabled=True,
        )
        
        # Data table for team members
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Prenom", weight="bold")),
                ft.DataColumn(ft.Text("Nom", weight="bold")),
                ft.DataColumn(ft.Text("Email", weight="bold")),
            ],
            rows=[],
            border=ft.Border.all(1, "#d0d0d0"),
            border_radius=8,
            horizontal_lines=ft.BorderSide(1, "#e0e0e0"),
            heading_row_color="#f5f5f5",
        )
        
        # Form container with vertical layout
        self.form_container = ft.Column(
            expand=True,
            spacing=20,
            controls=[
                # Header and file selector section
                ft.Column(
                    spacing=15,
                    controls=[
                        ft.Text("Form Creations", size=30, weight="bold", color="#1f2525"),
                        ft.Divider(height=1, color="#e0e0e0"),
                        
                        # CSV Section
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    padding=15,
                                    bgcolor="#f5f5f5",
                                    border_radius=8,
                                    content=ft.Column(
                                        spacing=10,
                                        controls=[
                                            ft.Text("Team CSV File", size=14, weight="bold", color="#1f2525"),
                                            ft.Text("Expected columns: Prenom, Nom, Email, Team", size=11, color="#666666"),
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
                                ft.Button(
                                    content="Reset",
                                    icon=ft.Icons.REFRESH,
                                    on_click=self.handle_reset,
                                ),
                            ]
                        ),
                    ]
                ),
                
                # Data Table section - full width
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                self.team_info_text,
                                ft.Row(
                                    spacing=5,
                                    controls=[
                                        self.prev_button,
                                        self.next_button,
                                    ]
                                ),
                            ]
                        ),
                        ft.Container(
                            padding=10,
                            bgcolor="white",
                            border=ft.Border.all(1, "#d0d0d0"),
                            border_radius=8,
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[self.data_table],
                            ),
                        ),
                        ft.Button(
                            content="Process Users",
                            icon=ft.Icons.CHECK,
                            on_click=self.handle_process_users,
                        ),
                    ]
                ),
            ]
        )
        
        self.controls = [self.form_container]
    
    def handle_process_users(self, e):
        print("=== Users in current team ===")
        for row in self.data_table.rows:
            prenom = row.cells[0].content.value
            nom = row.cells[1].content.value
            email = row.cells[2].content.value
            print(f"Prenom: {prenom}, Nom: {nom}, Email: {email}")
        print("=============================")
    
    def handle_prev_team(self, e):
        if self.current_team_index > 0:
            self.current_team_index -= 1
            self.display_current_team()
    
    def handle_next_team(self, e):
        if self.current_team_index < len(self.team_numbers) - 1:
            self.current_team_index += 1
            self.display_current_team()
    
    def display_current_team(self):
        if not self.team_numbers:
            return
        
        team_number = self.team_numbers[self.current_team_index]
        members = self.teams_data[team_number]
        
        # Update team info
        self.team_info_text.value = f"Team {team_number} ({self.current_team_index + 1}/{len(self.team_numbers)})"
        
        # Update navigation buttons
        self.prev_button.disabled = (self.current_team_index == 0)
        self.next_button.disabled = (self.current_team_index == len(self.team_numbers) - 1)
        
        # Update table
        self.data_table.rows.clear()
        for member in members:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(member['prenom'])),
                        ft.DataCell(ft.Text(member['nom'])),
                        ft.DataCell(ft.Text(member['email'])),
                    ]
                )
            )
        
        self.team_info_text.update()
        self.prev_button.update()
        self.next_button.update()
        self.data_table.update()
    
    async def handle_csv_pick(self, e):
        files = await ft.FilePicker().pick_files(
            allowed_extensions=["csv"],
            dialog_title="Pick a CSV file with team members"
        )
        if files:
            self.csv_file_path = files[0].path
            self.csv_file_name.value = f"✓ {files[0].name}"
            self.csv_file_name.color = "#4CAF50"
            
            # Load and organize CSV data by teams
            try:
                with open(files[0].path, 'r', encoding='utf-8') as f:
                    # Try to detect if file has headers
                    first_line = f.readline().strip()
                    f.seek(0)
                    
                    # Check if first line looks like headers
                    has_headers = 'prenom' in first_line.lower() or 'nom' in first_line.lower() or 'email' in first_line.lower()
                    
                    self.teams_data.clear()
                    
                    if has_headers:
                        csv_reader = csv.DictReader(f)
                        
                        for row in csv_reader:
                            prenom = row.get('Prenom', row.get('prenom', ''))
                            nom = row.get('Nom', row.get('nom', ''))
                            email = row.get('Email', row.get('email', ''))
                            team = row.get('Team', row.get('team', ''))
                            
                            if team not in self.teams_data:
                                self.teams_data[team] = []
                            
                            self.teams_data[team].append({
                                'prenom': prenom,
                                'nom': nom,
                                'email': email
                            })
                    else:
                        # No headers, assume columns are: Prenom, Nom, Email, Team
                        csv_reader = csv.reader(f)
                        
                        for row in csv_reader:
                            if len(row) >= 4:
                                prenom = row[0]
                                nom = row[1]
                                email = row[2]
                                team = row[3]
                                
                                if team not in self.teams_data:
                                    self.teams_data[team] = []
                                
                                self.teams_data[team].append({
                                    'prenom': prenom,
                                    'nom': nom,
                                    'email': email
                                })
                    
                    # Sort team numbers
                    self.team_numbers = sorted(self.teams_data.keys())
                    self.current_team_index = 0
                    
                    # Display first team
                    if self.team_numbers:
                        self.display_current_team()
                    
                self.csv_file_name.update()
            except:
                self.csv_file_name.value = "Error loading CSV file"
                self.csv_file_name.color = "#f44336"
                self.csv_file_name.update()

    async def handle_reset(self, e):
        self.csv_file_path = None
        self.csv_file_name.value = "No file selected"
        self.csv_file_name.color = "#666666"
        self.data_table.rows.clear()
        
        self.csv_file_name.update()
        self.data_table.update()