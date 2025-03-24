#!/bin/bash

# Launch script for Whisper Converter
# This script runs the application directly from Python source

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
else
    source venv/bin/activate
fi

# Run the application
echo "Starting Whisper Converter..."
python3 src/main.py

# Deactivate virtual environment when done
deactivate
