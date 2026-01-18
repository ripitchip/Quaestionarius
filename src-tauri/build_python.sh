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

# Get the target architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    TARGET_SUFFIX="x86_64-unknown-linux-gnu"
elif [ "$ARCH" = "aarch64" ]; then
    TARGET_SUFFIX="aarch64-unknown-linux-gnu"
else
    TARGET_SUFFIX="${ARCH}-unknown-linux-gnu"
fi

# Create binaries directory if it doesn't exist
mkdir -p binaries

# Copy executables with architecture suffix
echo "📦 Copying executables to binaries directory..."
cp src/python_bin/google_auth "binaries/google_auth-${TARGET_SUFFIX}"
cp src/python_bin/json_processor "binaries/json_processor-${TARGET_SUFFIX}"

# Deactivate virtual environment
deactivate

echo "✅ Python executables built successfully!"
