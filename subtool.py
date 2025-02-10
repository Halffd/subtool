#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run main
from src.main import main

if __name__ == "__main__":
    main() 