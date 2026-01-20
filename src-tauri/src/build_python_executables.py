#!/usr/bin/env python3
"""Build portable Python executables using PyInstaller"""

import subprocess
import os
import sys
import shutil
import platform
from pathlib import Path

# Get paths relative to script location
SCRIPT_DIR = Path(__file__).parent
TAURI_DIR = SCRIPT_DIR.parent
BUILD_DIR = TAURI_DIR / "python_build"
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
    
    # -c ensures Console mode so stdout works for Tauri
    # Removed --nopreview which caused the error
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "-c", 
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "build"),
        "--specpath", str(BUILD_DIR),
        "--name", output_name,
        str(script_path),
    ]
    
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
    print("🚀 Building portable Python executables...")
    
    # Core imports to ensure the binary doesn't crash silently
    core_imports = ["json", "sys", "pathlib"]
    google_auth_imports = core_imports + [
        "google_auth_oauthlib",
        "google_auth_oauthlib.flow",
        "googleapiclient",
        "googleapiclient.discovery",
        "google.auth",
        "google.auth.transport.requests",
    ]
    
    success = True
    success &= build_executable("google_auth", "google_auth", google_auth_imports)
    success &= build_executable("json_processor", "json_processor", core_imports)
    
    if success:
        FINAL_BIN_DIR = TAURI_DIR / "binaries"
        FINAL_BIN_DIR.mkdir(exist_ok=True)
        
        machine = platform.machine()
        suffix_map = {
            "x86_64": "x86_64-unknown-linux-gnu",
            "aarch64": "aarch64-unknown-linux-gnu",
            "arm64": "aarch64-apple-darwin"
        }
        suffix = suffix_map.get(machine, f"{machine}-unknown-linux-gnu")

        for exe_file in DIST_DIR.glob("*"):
            if exe_file.is_file():
                dest = FINAL_BIN_DIR / f"{exe_file.name}-{suffix}"
                shutil.copy2(exe_file, dest)
                os.chmod(dest, 0o755)
                print(f"📦 Sidecar ready: {dest.name}")
    else:
        print("\n❌ Build failed")
        sys.exit(1)

if __name__ == "__main__":
    main()