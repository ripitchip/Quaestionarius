from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import pickle
import json
import sys
import io
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file"
]


def get_storage_dir() -> Path:
    """Get the storage directory for credentials."""
    storage_dir = Path.home() / ".queastonarius"
    storage_dir.mkdir(exist_ok=True)
    return storage_dir


def authenticate_google() -> dict:
    """
    Authenticate with Google using saved credentials.json.
    
    Returns:
        dict: Authentication status and message
    """
    try:
        storage_dir = get_storage_dir()
        credentials_file = storage_dir / "credentials.json"
        token_file = storage_dir / "token.pickle"
        
        if not credentials_file.exists():
            return {
                "status": "error",
                "message": "No credentials.json found. Please save your credentials first."
            }
        
        creds = None
        
        # Load existing token if available
        if token_file.exists():
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
        
        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file), SCOPES
                )
                # Suppress browser opening message by redirecting stderr
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()
                try:
                    creds = flow.run_local_server(port=0, open_browser=True)
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
            
            # Save the credentials for the next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
        
        # Test the connection by building the service
        forms_service = build("forms", "v1", credentials=creds)
        
        return {
            "status": "success",
            "message": "Successfully authenticated with Google",
            "token_saved": str(token_file)
        }
        
    except FileNotFoundError as e:
        return {
            "status": "error",
            "message": f"File not found: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Authentication failed: {str(e)}"
        }


def check_auth_status() -> dict:
    """
    Check if user is already authenticated.
    
    Returns:
        dict: Authentication status
    """
    try:
        storage_dir = get_storage_dir()
        token_file = storage_dir / "token.pickle"
        credentials_file = storage_dir / "credentials.json"
        
        has_credentials = credentials_file.exists()
        has_token = token_file.exists()
        
        if has_token:
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
                is_valid = creds and creds.valid
                
                return {
                    "status": "authenticated" if is_valid else "expired",
                    "has_credentials": has_credentials,
                    "has_token": has_token,
                    "is_valid": is_valid
                }
        
        return {
            "status": "not_authenticated",
            "has_credentials": has_credentials,
            "has_token": has_token,
            "is_valid": False
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "authenticate":
        result = authenticate_google()
        print(json.dumps(result, indent=2))
    elif command == "check_status":
        result = check_auth_status()
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)
