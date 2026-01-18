#!/usr/bin/env python3
"""Build portable Python executables using PyInstaller"""

import subprocess
import os
import sys
import platform
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
BUILD_DIR = SCRIPT_DIR / "python_executables"
DIST_DIR = BUILD_DIR / "dist"

# Create build directory
BUILD_DIR.mkdir(exist_ok=True)

# Determine target triple for the current platform
def get_target_triple():
    """Get the Rust target triple for the current platform"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map Python's machine names to Rust's
    if machine in ['x86_64', 'amd64']:
        machine = 'x86_64'
    elif machine in ['aarch64', 'arm64']:
        machine = 'aarch64'
    
    if system == 'linux':
        return f"{machine}-unknown-linux-gnu"
    elif system == 'darwin':
        return f"{machine}-apple-darwin"
    elif system == 'windows':
        return f"{machine}-pc-windows-msvc"
    else:
        return f"{machine}-unknown-{system}"

def build_executable(script_name: str, output_name: str):
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
        "--console",  # Console mode to allow stdin/stdout
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "build"),
        "--specpath", str(BUILD_DIR),
        "--name", output_name,
        "--collect-all", "google",
        "--collect-all", "google_auth_oauthlib",
        "--collect-all", "google_auth",
        "--collect-all", "googleapiclient",
        "--collect-all", "requests_oauthlib",
        "--collect-all", "requests",
        "--hidden-import=pkg_resources",
        "--noconfirm",
        str(script_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error building {output_name}:")
        print(result.stderr)
        print(result.stdout)
        return False
    
    print(f"✅ Built {output_name}")
    return True

def main():
    """Build all Python executables"""
    print("🚀 Building portable Python executables...")
    
    success = True
    success &= build_executable("google_auth", "google_auth")
    success &= build_executable("json_processor", "json_processor")
    
    if success:
        print(f"\n✅ All executables built successfully in {DIST_DIR}")
        
        # Copy executables to the binaries folder with target triple suffix
        # Tauri expects binaries at src-tauri/binaries/<name>-<target-triple>
        target_triple = get_target_triple()
        OUTPUT_DIR = SCRIPT_DIR.parent / "binaries"
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        for exe_file in DIST_DIR.glob("*"):
            if exe_file.is_file():
                # Add target triple to the filename
                dest = OUTPUT_DIR / f"{exe_file.stem}-{target_triple}"
                import shutil
                shutil.copy2(exe_file, dest)
                # Make sure it's executable
                os.chmod(dest, 0o755)
                print(f"📦 Copied to {dest}")
    else:
        print("\n❌ Build failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
