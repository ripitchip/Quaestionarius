#!/usr/bin/env python3
"""Build portable Python executables using PyInstaller"""

import subprocess
import os
import sys
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
BUILD_DIR = SCRIPT_DIR / "python_executables"
DIST_DIR = BUILD_DIR / "dist"

# Create build directory
BUILD_DIR.mkdir(exist_ok=True)

def build_executable(script_name: str, output_name: str, hidden_imports=None):
    """Build a single executable with PyInstaller"""
    script_path = SCRIPT_DIR / f"{script_name}.py"
    
    if not script_path.exists():
        print(f"Error: {script_path} not found")
        return False
    
    print(f"\n🔨 Building {output_name}...")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "build"),
        "--specpath", str(BUILD_DIR),
        "--name", output_name,
        str(script_path),
    ]
    
    # Add hidden imports if provided
    if hidden_imports:
        for module in hidden_imports:
            cmd.extend(["--hidden-import", module])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error building {output_name}:")
        print(result.stderr)
        return False
    
    print(f"✅ Built {output_name}")
    return True

def main():
    """Build all Python executables"""
    print("🚀 Building portable Python executables...")
    
    # Hidden imports for google_auth
    google_auth_imports = [
        "google_auth_oauthlib",
        "google_auth_oauthlib.flow",
        "googleapiclient",
        "googleapiclient.discovery",
        "google.auth",
        "google.auth.transport",
        "google.auth.transport.requests",
        "google.oauth2",
        "google.oauth2.credentials",
        "pickle",
        "requests_oauthlib",
    ]
    
    success = True
    success &= build_executable("google_auth", "google_auth", google_auth_imports)
    success &= build_executable("json_processor", "json_processor")
    
    if success:
        print(f"\n✅ All executables built successfully in {DIST_DIR}")
        
        # Copy executables to a more accessible location
        OUTPUT_DIR = SCRIPT_DIR / "python_bin"
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        for exe_file in DIST_DIR.glob("*"):
            if exe_file.is_file():
                dest = OUTPUT_DIR / exe_file.name
                import shutil
                shutil.copy2(exe_file, dest)
                print(f"📦 Copied to {dest}")
    else:
        print("\n❌ Build failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
