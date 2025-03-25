#!/bin/bash
# Script to run subtool with proper environment setup

# Change to the directory containing this script
cd "$(dirname "$0")" || exit 1

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python && ! command_exists python3; then
  echo "Error: Python is not installed. Please install Python 3.6 or higher."
  exit 1
fi

# Use either python or python3 command
PYTHON_CMD="python"
if ! command_exists python; then
  PYTHON_CMD="python3"
fi

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON_CMD -m venv venv
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment. Please install venv module."
    echo "Try: $PYTHON_CMD -m pip install --user virtualenv"
    exit 1
  fi
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
  echo "Activating virtual environment..."
  # shellcheck disable=SC1091
  source venv/bin/activate
else
  echo "Error: Virtual environment activation script not found."
  exit 1
fi

# Install dependencies if requirements file exists
if [ -f "requirements.txt" ]; then
  echo "Checking dependencies..."
  pip install -r requirements.txt
  if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
  fi
else
  # If no requirements file, install minimal required packages
  echo "Installing minimal required dependencies..."
  pip install PyQt6
  if [ $? -ne 0 ]; then
    echo "Error: Failed to install PyQt6."
    exit 1
  fi
fi

# Set environment variables for Qt on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Try to locate Qt plugins directory
  for qt_plugin_path in \
    /usr/lib/qt/plugins \
    /usr/lib/qt6/plugins \
    /usr/lib/x86_64-linux-gnu/qt6/plugins \
    /usr/local/lib/qt6/plugins \
    /usr/lib64/qt6/plugins; do
    if [ -d "$qt_plugin_path" ]; then
      export QT_PLUGIN_PATH="$qt_plugin_path"
      echo "Set QT_PLUGIN_PATH to $qt_plugin_path"
      break
    fi
  done
  
  # Disable high DPI scaling
  export QT_AUTO_SCREEN_SCALE_FACTOR=1
fi

# Run the application
echo "Starting Subtitle Merger Tool..."
python subtool.py "$@" 