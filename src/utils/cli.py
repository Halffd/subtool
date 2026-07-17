#!/usr/bin/env python3
"""
Enhanced CLI Interface for Subtitle Merger Tool
This module provides backward compatibility with the old CLI while supporting new features
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    # Import the enhanced CLI interface
    from src.cli_interface import main as enhanced_main
    enhanced_main()

if __name__ == "__main__":
    main()

