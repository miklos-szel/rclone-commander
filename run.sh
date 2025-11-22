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

# Activate venv
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/upgrade requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# If a remote argument is provided, update the config
if [ -n "$1" ]; then
    echo "Setting default remote to: $1"
    if [ -f "config/app_config.ini" ]; then
        # Update the config file with the specified remote
        sed -i.bak "s/^default_left_remote = .*/default_left_remote = $1/" config/app_config.ini
    fi
fi

# Run the application
echo "Starting Rclone Commander..."
python3 -m src.rclone_commander.main

# Deactivate venv on exit
deactivate
