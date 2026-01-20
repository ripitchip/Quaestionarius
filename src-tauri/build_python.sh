#!/bin/bash
set -e

echo "🔨 Preparing Python Sidecars..."

# Navigate to the src-tauri directory
cd "$(dirname "$0")"

# 1. Setup Venv
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# 2. Get Venv Python path
VENV_PYTHON="$(pwd)/.venv/bin/python"

# 3. Install Requirements
echo "📦 Installing requirements..."
${VENV_PYTHON} -m pip install --upgrade pip
${VENV_PYTHON} -m pip install pyinstaller
if [ -f "requirements.txt" ]; then
    ${VENV_PYTHON} -m pip install -r requirements.txt
fi

# 4. Run the Builder
# Assuming the python builder is in src/build_python_executables.py
${VENV_PYTHON} src/build_python_executables.py

echo "✅ Sidecars are ready in src-tauri/binaries/"