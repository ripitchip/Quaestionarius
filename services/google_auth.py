"""Google Authentication Service for handling OAuth flow and credentials management."""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pathlib import Path

# Define the scopes your application needs
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file"
]

# Paths for storing credentials and tokens
DATA_DIR = Path(os.path.expanduser("~/.quaestionarius"))
CREDENTIALS_PATH = DATA_DIR / "credentials.json"
TOKEN_PATH = DATA_DIR / "token.pickle"


class GoogleAuthService:
    """Handles Google OAuth2 authentication and credential management."""
    
    def __init__(self):
        """Initialize the authentication service."""
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.creds = None
        self.forms_service = None
    
    @staticmethod
    def credentials_file_exists() -> bool:
        """Check if credentials.json file exists."""
        return CREDENTIALS_PATH.exists()
    
    @staticmethod
    def token_file_exists() -> bool:
        """Check if token.pickle file exists."""
        return TOKEN_PATH.exists()
    
    def load_token_from_pickle(self) -> bool:
        """Load credentials from pickle file if available."""
        if TOKEN_PATH.exists():
            try:
                with open(TOKEN_PATH, "rb") as token_file:
                    self.creds = pickle.load(token_file)
                return True
            except Exception as e:
                print(f"Error loading token: {e}")
                return False
        return False
    
    def refresh_credentials(self) -> bool:
        """Refresh expired credentials."""
        try:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                self._save_token_to_pickle()
                return True
        except Exception as e:
            print(f"Error refreshing credentials: {e}")
        return False
    
    def _save_token_to_pickle(self) -> bool:
        """Save credentials to pickle file."""
        try:
            with open(TOKEN_PATH, "wb") as token_file:
                pickle.dump(self.creds, token_file)
            return True
        except Exception as e:
            print(f"Error saving token: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Perform OAuth2 authentication flow.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"credentials.json not found at {CREDENTIALS_PATH}. "
                f"Please upload your credentials.json file."
            )
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            # Run local server for OAuth flow
            self.creds = flow.run_local_server(port=0)
            self._save_token_to_pickle()
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self.creds:
            return False
        
        if self.creds.expired and self.creds.refresh_token:
            return self.refresh_credentials()
        
        return self.creds.valid
    
    def get_authenticated_service(self, service_name: str = "forms"):
        """
        Get an authenticated Google API service.
        
        Args:
            service_name: The service to build (default: "forms")
            
        Returns:
            Google API service object or None if not authenticated
        """
        if not self.is_authenticated():
            return None
        
        try:
            from googleapiclient.discovery import build
            return build(service_name, "v1", credentials=self.creds)
        except Exception as e:
            print(f"Error building service: {e}")
            return None
    
    def logout(self) -> bool:
        """Logout and remove stored credentials."""
        try:
            self.creds = None
            self.forms_service = None
            
            # Remove pickle token
            if TOKEN_PATH.exists():
                TOKEN_PATH.unlink()
            
            return True
        except Exception as e:
            print(f"Error during logout: {e}")
            return False
    
    def get_user_info(self) -> dict:
        """Get authenticated user information."""
        if not self.is_authenticated():
            return {}
        
        try:
            # Get user info from credentials
            return {
                "email": getattr(self.creds, 'client_id', 'Unknown'),
                "token_expiry": str(self.creds.expiry) if self.creds.expiry else "Never",
            }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {}
