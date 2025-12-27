#!/bin/bash
# Script to activate virtual environment and run stats.py

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Path to your virtual environment (adjust this path as needed)
VENV_PATH="./pihole"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create a virtual environment first with: python3 -m venv pihole"
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Run the stats.py script
echo "Running stats.py..."
python stats.py

# Deactivate is automatic when script exits, but you can uncomment if needed
# deactivate
