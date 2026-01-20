import os
import sys
import io
import json
import pickle
import platform
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Scopes for Google Forms and Drive
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file"
]

def get_storage_dir() -> Path:
    """Get the official AppData directory matching Tauri's BaseDirectory.AppData"""
    system = platform.system()
    if system == "Windows":
        base_dir = Path(os.getenv("LOCALAPPDATA")) / "com.vscode.queastonarius"
    elif system == "Darwin":
        base_dir = Path.home() / "Library" / "Application Support" / "com.vscode.queastonarius"
    else:
        # Linux standard matching your environment
        base_dir = Path.home() / ".local" / "share" / "com.vscode.queastonarius"
    
    (base_dir / "templates").mkdir(parents=True, exist_ok=True)
    return base_dir

def get_google_service():
    storage_dir = get_storage_dir()
    token_file = storage_dir / "token.pickle"
    if not token_file.exists():
        return None
    with open(token_file, "rb") as token:
        creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("forms", "v1", credentials=creds)

def authenticate_google(credentials_path: str = None) -> dict:
    original_stdout, original_stderr = sys.stdout, sys.stderr
    try:
        storage_dir = get_storage_dir()
        # Use provided path or look in AppData
        credentials_file = Path(credentials_path) if credentials_path else storage_dir / "credentials.json"
        token_file = storage_dir / "token.pickle"

        if not credentials_file.exists():
            return {"status": "error", "message": f"Credentials not found at {credentials_file}"}
        
        creds = None
        if token_file.exists():
            try:
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)
            except: creds = None
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try: creds.refresh(Request())
                except: creds = None
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
                sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
                try:
                    creds = flow.run_local_server(port=0, open_browser=True, timeout_seconds=60)
                finally:
                    sys.stdout, sys.stderr = original_stdout, original_stderr
            
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
                
        return {"status": "success", "message": "Authenticated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_forms(template_name: str, group_name: str, participants_json: str) -> dict:
    try:
        service = get_google_service()
        if not service: return {"status": "error", "message": "Not authenticated"}

        template_path = get_storage_dir() / "templates" / f"{template_name}.json"
        with open(template_path, 'r', encoding='utf-8') as f:
            template_raw = f.read()

        participants = json.loads(participants_json)
        results = []

        for p in participants:
            full_name = f"{p['Name']} {p['LastName']}"
            colleagues = [f"{o['Name']} {o['LastName']}" for o in participants if o['id'] != p['id']]
            processed = template_raw.replace("{{group_name}}", group_name).replace("{{member_name}}", full_name)
            data = json.loads(processed)

            form_body = {"info": {"title": f"{data.get('name', 'Form')} - {full_name}"}}
            new_form = service.forms().create(body=form_body).execute()
            
            requests = data.get("requests", [])
            for req in requests:
                try:
                    grid = req["createItem"]["item"]["questionItem"]["question"]["gridQuestion"]
                    if grid["rows"]["options"] == "{{colleagues_list}}":
                        grid["rows"]["options"] = [{"value": name} for name in colleagues]
                except: pass

            service.forms().batchUpdate(formId=new_form['formId'], body={"requests": requests}).execute()
            results.append({"participant": full_name, "url": new_form['responderUri']})

        return {"status": "success", "forms": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_auth_status() -> dict:
    token_file = get_storage_dir() / "token.pickle"
    if token_file.exists():
        with open(token_file, "rb") as token:
            creds = pickle.load(token)
            return {"status": "authenticated" if creds and creds.valid else "expired"}
    return {"status": "not_authenticated"}

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2: sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "authenticate":
        print(json.dumps(authenticate_google(sys.argv[2] if len(sys.argv) > 2 else None)))
    elif cmd == "check_status":
        print(json.dumps(check_auth_status()))
    elif cmd == "generate":
        print(json.dumps(generate_forms(sys.argv[2], sys.argv[3], sys.argv[4])))