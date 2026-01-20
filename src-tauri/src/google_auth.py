import os
import sys
import io
import json
import pickle
import platform
from datetime import datetime
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file"
]

def get_storage_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base_dir = Path(os.getenv("LOCALAPPDATA")) / "com.vscode.queastonarius"
    elif system == "Darwin":
        base_dir = Path.home() / "Library" / "Application Support" / "com.vscode.queastonarius"
    else:
        base_dir = Path.home() / ".local" / "share" / "com.vscode.queastonarius"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def get_services():
    storage_dir = get_storage_dir()
    token_file = storage_dir / "token.pickle"
    if not token_file.exists():
        return None, None
    with open(token_file, "rb") as token:
        creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("forms", "v1", credentials=creds), build("drive", "v3", credentials=creds)

def authenticate_google(credentials_path=None):
    try:
        storage_dir = get_storage_dir()
        creds_file = Path(credentials_path) if credentials_path else storage_dir / "credentials.json"
        token_file = storage_dir / "token.pickle"

        if not creds_file.exists():
            return {"status": "error", "message": "credentials.json not found"}

        flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)
        return {"status": "success", "message": "Authenticated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_auth_status():
    token_file = get_storage_dir() / "token.pickle"
    if token_file.exists():
        return {"status": "authenticated"}
    return {"status": "not_authenticated"}

def get_or_create_parent_folder(drive_service):
    """Finds or creates the master 'queastonarius' folder."""
    query = "name = 'queastonarius' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = drive_service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    files = response.get('files', [])
    
    if files:
        return files[0].get('id')
    else:
        folder_meta = {
            'name': 'queastonarius',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_meta, fields='id').execute()
        return folder.get('id')

def batch_generate(template_name, group_data_json, variables_json):
    try:
        forms_service, drive_service = get_services()
        if not forms_service:
            return {"status": "error", "message": "Authentication required"}

        groups = json.loads(group_data_json)
        vars_dict = json.loads(variables_json)
        max_val = vars_dict.get("max_value", "10")
        prompt = vars_dict.get("prompt_text", "").replace("{{max_value}}", max_val)

        # 1. Get or Create the MASTER folder
        master_folder_id = get_or_create_parent_folder(drive_service)

        # 2. Create the SESSION folder INSIDE the master folder
        session_folder_meta = {
            'name': f"Potatoes Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [master_folder_id] # This puts it inside queastonarius immediately
        }
        session_folder = drive_service.files().create(body=session_folder_meta, fields='id, webViewLink').execute()
        session_folder_id = session_folder.get('id')

        results = []
        for group_name, members in groups.items():
            # 3. Create the Form
            form_title = f"Team Evaluation: {group_name}"
            form_body = {
                "info": {
                    "title": form_title,
                    "documentTitle": form_title 
                }
            }
            new_form = forms_service.forms().create(body=form_body).execute()
            f_id = new_form['formId']

            # 4. Move Form to the SESSION folder
            f_file = drive_service.files().get(fileId=f_id, fields='parents').execute()
            previous_parents = ",".join(f_file.get('parents', []))
            
            drive_service.files().update(
                fileId=f_id, 
                addParents=session_folder_id, 
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            # 5. Add Questions
            requests = [
                {"updateFormInfo": {"info": {"description": prompt}, "updateMask": "description"}}
            ]
            for i, member in enumerate(members):
                full_name = f"{member['Name']} {member['LastName']}"
                requests.append({
                    "createItem": {
                        "item": {
                            "title": f"Patates pour / Potatoes for: {full_name}",
                            "questionItem": {"question": {"required": True, "textQuestion": {"paragraph": False}}}
                        },
                        "location": {"index": i}
                    }
                })

            forms_service.forms().batchUpdate(formId=f_id, body={"requests": requests}).execute()
            results.append({"group": group_name, "url": new_form.get('responderUri')})

        return {
            "status": "success", 
            "forms": results, 
            "folder_url": session_folder.get('webViewLink')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_sessions():
    """Lists subfolders inside the master 'queastonarius' folder."""
    try:
        _, drive_service = get_services()
        master_id = get_or_create_parent_folder(drive_service)
        
        query = f"'{master_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name, createdTime)").execute()
        return {"status": "success", "sessions": results.get('files', [])}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_session_results(session_folder_id):
    """Aggregates responses from all forms within a session folder."""
    try:
        forms_service, drive_service = get_services()
        
        query = f"'{session_folder_id}' in parents and mimeType = 'application/vnd.google-apps-form' and trashed = false"
        forms_in_session = drive_service.files().list(q=query, fields="files(id, name)").execute().get('files', [])
        
        all_results = []
        for f in forms_in_session:
            form_id = f['id']
            # Map Question IDs to Titles
            form_meta = forms_service.forms().get(formId=form_id).execute()
            question_map = {q['question']['questionId']: item['title'] 
                           for item in form_meta.get('items', []) 
                           if 'questionItem' in item 
                           for q in [item['questionItem']]}
            
            responses = forms_service.forms().responses().list(formId=form_id).execute().get('responses', [])
            for resp in responses:
                entry = {"form_name": f['name'], "timestamp": resp['createTime']}
                for q_id, answer in resp['answers'].items():
                    val = answer['textAnswers']['answers'][0]['value']
                    entry[question_map.get(q_id, "Unknown")] = val
                all_results.append(entry)
                
        return {"status": "success", "data": all_results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    try:
        cmd = sys.argv[1]
        if cmd == "list_sessions":
            print(json.dumps(list_sessions()))
        elif cmd == "get_session_results":
            print(json.dumps(get_session_results(sys.argv[2])))
        elif cmd == "batch_generate":
            print(json.dumps(batch_generate(sys.argv[2], sys.argv[3], sys.argv[4])))
        elif cmd == "authenticate":
            print(json.dumps(authenticate_google(sys.argv[2] if len(sys.argv) > 2 else None)))
        elif cmd == "check_status":
            print(json.dumps(check_auth_status()))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))