#!/usr/bin/env python3
"""Initialize Python environment for the application"""

import subprocess
import sys
import os
from pathlib import Path

def setup_environment():
    """Create and setup virtual environment with dependencies"""
    
    # Get the directory where this script is located
    app_dir = Path(__file__).parent
    venv_dir = app_dir / "venv"
    
    # Check if venv already exists
    if venv_dir.exists():
        print(f"Virtual environment already exists at {venv_dir}")
        return str(venv_dir / "bin" / "python")
    
    print(f"Creating virtual environment at {venv_dir}...")
    
    # Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    
    # Upgrade pip
    pip_executable = venv_dir / "bin" / "pip"
    subprocess.run([str(pip_executable), "install", "--upgrade", "pip"], check=True)
    
    # Install requirements
    requirements_file = app_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"Installing requirements from {requirements_file}...")
        subprocess.run([str(pip_executable), "install", "-r", str(requirements_file)], check=True)
    
    print("✅ Environment setup complete!")
    return str(venv_dir / "bin" / "python")

if __name__ == "__main__":
    python_exe = setup_environment()
    print(python_exe)
