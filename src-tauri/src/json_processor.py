import json
import sys
from pathlib import Path


def validate_json_file(file_path: str) -> dict:
    """
    Validate and read a JSON file, returning its contents.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        dict: Result with status and either data or error
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {
                "status": "error",
                "message": f"File not found: {file_path}"
            }
        
        if not path.is_file():
            return {
                "status": "error",
                "message": f"Path is not a file: {file_path}"
            }
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate it's a valid Google OAuth credentials file
        if "installed" not in data and "web" not in data:
            return {
                "status": "error",
                "message": "Invalid credentials file format. Expected 'installed' or 'web' key."
            }
        
        return {
            "status": "success",
            "message": "Valid credentials file",
            "data": data
        }
        
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No file path provided"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = validate_json_file(file_path)
    print(json.dumps(result, indent=2))