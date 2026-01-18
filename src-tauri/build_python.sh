#!/bin/bash
set -e

echo "🔨 Building Python executables with PyInstaller..."

cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q pyinstaller

# Run the build script
python3 src/build_python_executables.py

# Deactivate virtual environment
deactivate

echo "✅ Python executables built successfully!"
