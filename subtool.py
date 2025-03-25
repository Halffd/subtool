#!/usr/bin/env python3
"""
Subtitle Merger Tool - Main entry point
"""

import sys
import os
import traceback
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def main():
    try:
        # Import and run the main function from src.main
        from src.main import main as app_main
        
        # Set up QT environment variables if needed
        if sys.platform.startswith('linux'):
            # Try to locate the Qt platform plugins
            potential_plugin_paths = [
                '/usr/lib/qt/plugins',
                '/usr/lib/qt6/plugins',
                '/usr/lib/x86_64-linux-gnu/qt6/plugins',
                '/usr/local/lib/qt6/plugins',
                '/usr/lib64/qt6/plugins'
            ]
            
            for path in potential_plugin_paths:
                if os.path.exists(path):
                    os.environ['QT_PLUGIN_PATH'] = path
                    print(f"Set QT_PLUGIN_PATH to {path}")
                    break
        
        # Run the application
        app_main()
        
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you have installed all required dependencies.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 