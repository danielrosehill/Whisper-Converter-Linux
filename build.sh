#!/bin/bash

# Build script for Whisper Converter
# This script builds a standalone executable using PyInstaller

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install pyinstaller
else
    source venv/bin/activate
    # Make sure pyinstaller is installed
    pip install pyinstaller
fi

# Clean previous build if it exists
if [ -d "dist" ]; then
    echo "Cleaning previous build..."
    rm -rf dist build
fi

echo "Building Whisper Converter executable..."
pyinstaller --name="WhisperConverter" \
            --onefile \
            --windowed \
            --add-data="src:src" \
            --icon=NONE \
            src/main.py

echo ""
if [ -f "dist/WhisperConverter" ]; then
    echo "Build successful! Executable is located at: dist/WhisperConverter"
    echo "You can run it with: ./dist/WhisperConverter"
else
    echo "Build failed. Check the output for errors."
fi

# Deactivate virtual environment when done
deactivate
