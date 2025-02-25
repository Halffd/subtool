#!/bin/bash

# Set Qt platform plugin path
export QT_PLUGIN_PATH=/usr/lib/qt/plugins
export QT_QPA_PLATFORM=xcb

# Run the application
python -m src.main 