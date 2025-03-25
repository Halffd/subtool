#!/usr/bin/env python
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
import logging

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Qt platform plugin path
if sys.platform.startswith('linux'):
    potential_plugin_paths = [
        '/usr/lib/qt/plugins',
        '/usr/lib/qt6/plugins',
        '/usr/lib/x86_64-linux-gnu/qt6/plugins',
        '/usr/local/lib/qt6/plugins'
    ]
    for path in potential_plugin_paths:
        if os.path.exists(path):
            os.environ['QT_PLUGIN_PATH'] = path
            break

# Import our modules
from src.utils.pattern_guesser import suggest_patterns
from src.utils.pattern_dialog import PatternConflictDialog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_conflict_resolution():
    """Test the pattern conflict resolution dialog."""
    app = QApplication(sys.argv)
    
    # Get pattern suggestions and conflicts
    result = suggest_patterns("test_subs", logger)
    
    if 'error' in result:
        logger.error(f"Error: {result['error']}")
        return
    
    conflicts = result.get('conflicts', {})
    if not conflicts:
        logger.info("No conflicts detected")
        return
    
    logger.info(f"Found {len(conflicts)} pattern conflicts")
    
    # Show dialog for each conflict
    for conflict_key, conflict_data in conflicts.items():
        logger.info(f"\nResolving conflict for episode {conflict_data['episode']} ({conflict_data['language']})")
        
        # Show the dialog
        selected = PatternConflictDialog.resolve_conflicts(conflict_data)
        
        if selected:
            logger.info(f"Selected pattern: {selected['pattern']}")
            logger.info("Matching files:")
            for match in selected['matches']:
                logger.info(f"  - {Path(match).name}")
        else:
            logger.info("No pattern selected (dialog cancelled)")

if __name__ == "__main__":
    test_conflict_resolution() 