#!/bin/bash
set -e

echo "🔨 Building Python executables with PyInstaller..."

cd "$(dirname "$0")"

# Run the build script
python3 src/build_python_executables.py

echo "✅ Python executables built successfully!"
