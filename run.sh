#!/bin/bash
# Wrapper script to run rclonecommander in a virtual environment
# Usage: ./run.sh [remote_name]

VENV_DIR="venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Use venv's python and pip directly (more reliable than activation)
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip3"

# Install/upgrade requirements
echo "Installing requirements..."
"$VENV_PIP" install -q -r requirements.txt

# If a remote argument is provided, update the config
if [ -n "$1" ]; then
    echo "Setting default remote to: $1"
    if [ -f "config/rclone-commander.ini" ]; then
        # Update the config file with the specified remote
        sed -i.bak "s/^default_left_remote = .*/default_left_remote = $1/" config/rclone-commander.ini
    fi
fi

# Run the application
echo "Starting Rclone Commander..."
"$VENV_PYTHON" -m src.rclone_commander.main
