#!/bin/bash
set -e

echo "🔨 Building Python executables with PyInstaller..."

cd "$(dirname "$0")"

## Ensure a usable Python is available
if command -v python3 >/dev/null 2>&1; then
    SYSTEM_PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    SYSTEM_PYTHON=python
else
    echo "❌ No Python interpreter found. Install Python 3 and try again."
    exit 1
fi

echo "📦 Using system Python: ${SYSTEM_PYTHON}"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    if command -v virtualenv >/dev/null 2>&1; then
        virtualenv .venv
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv
    elif command -v python >/dev/null 2>&1; then
        python -m venv .venv
    else
        echo "❌ Neither virtualenv nor python3 -m venv found. Please install one of them and try again."
        exit 1
    fi
fi

# Use the venv's python binary directly to avoid relying on an activated shell
VENV_PYTHON=""
VENV_DIR="$(pwd)/.venv/bin"
if [ -d "$VENV_DIR" ]; then
    for candidate in "$VENV_DIR"/python*; do
        # accept files and symlinks (use -e), not directories
        if [ -e "$candidate" ] && [ ! -d "$candidate" ]; then
            VENV_PYTHON="$candidate"
            break
        fi
    done
fi

if [ -z "$VENV_PYTHON" ]; then
    # fallback for Windows-style venv created on Windows host
    if [ -x "$(pwd)/.venv/Scripts/python.exe" ]; then
        VENV_PYTHON="$(pwd)/.venv/Scripts/python.exe"
    else
        echo "❌ No python executable found in .venv. Listing .venv directory for debugging:"
        ls -la "$(pwd)/.venv" || true
        ls -la "$(pwd)/.venv/bin" || true
        exit 1
    fi
fi

# If the candidate is a symlink, resolve and prefer the resolved executable if necessary
if [ ! -x "$VENV_PYTHON" ]; then
    if command -v readlink >/dev/null 2>&1; then
        RESOLVED=$(readlink -f "$VENV_PYTHON" 2>/dev/null || true)
        if [ -n "$RESOLVED" ] && [ -x "$RESOLVED" ]; then
            VENV_PYTHON="$RESOLVED"
        fi
    fi
fi

if [ ! -x "$VENV_PYTHON" ]; then
    echo "❌ Found $VENV_PYTHON but it is not executable. Listing .venv/bin for debugging:"
    ls -la "$(pwd)/.venv/bin" || true
    exit 1
fi

echo "📦 Using venv python: ${VENV_PYTHON}"

echo "📦 Installing Python dependencies into .venv..."
# Always use venv python for install/build steps (zsh/bash compatible)
${VENV_PYTHON} -m ensurepip --upgrade >/dev/null 2>&1 || true
${VENV_PYTHON} -m pip install -q --upgrade pip
${VENV_PYTHON} -m pip install -q -r requirements.txt
${VENV_PYTHON} -m pip install -q pyinstaller

# Run the build script using the venv python
${VENV_PYTHON} src/build_python_executables.py

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

# No need to call deactivate because we never activated the venv in this shell

echo "✅ Python executables built successfully!"
