#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtCore import Qt

# Add project root to Python path when run directly
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from src.tabs.directory_tab import DirectoryTab
from src.tabs.single_files_tab import SingleFilesTab

# Attempt to fix QT platform plugin issues
def setup_environment():
    """Set up environment variables for QT plugins"""
    if sys.platform.startswith('linux'):
        # Try to locate the Qt platform plugins
        potential_plugin_paths = [
            '/usr/lib/qt/plugins',
            '/usr/lib/qt6/plugins',
            '/usr/lib/x86_64-linux-gnu/qt6/plugins',
            '/usr/local/lib/qt6/plugins'
        ]
        
        for path in potential_plugin_paths:
            if os.path.exists(path):
                os.environ['QT_PLUGIN_PATH'] = path
                print(f"Set QT_PLUGIN_PATH to {path}")
                break
    
    # Disable high DPI scaling if needed
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Merger")
        
        # Set window attributes for dark title bar (platform specific)
        if sys.platform == "win32":
            # Windows specific dark title bar
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        elif sys.platform == "darwin":
            # macOS specific dark title bar
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setUnifiedTitleAndToolBarOnMac(True)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        try:
            # Add tabs and catch exceptions individually for each tab
            try:
                single_files_tab = SingleFilesTab()
                self.tabs.addTab(single_files_tab, "Single Files")
            except Exception as e:
                print(f"Error loading Single Files tab: {e}")
                import traceback
                traceback.print_exc()
            
            try:
                directory_tab = DirectoryTab()
                self.tabs.addTab(directory_tab, "Directory")
            except Exception as e:
                print(f"Error loading Directory tab: {e}")
                import traceback
                traceback.print_exc()
            
            # Check if no tabs were added
            if self.tabs.count() == 0:
                raise Exception("No tabs could be loaded")
                
        except Exception as e:
            print(f"Error initializing tabs: {e}")
            QMessageBox.critical(self, "Error", f"Error initializing tabs: {e}")
        
        # Set central widget
        self.setCentralWidget(self.tabs)
        
        # Set initial size
        self.resize(800, 600)

def main():
    # Fix QT plugin paths
    setup_environment()
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")
    
    try:
        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Start the event loop
        sys.exit(app.exec())
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        # Show error using QMessageBox if possible
        if QApplication.instance():
            QMessageBox.critical(None, "Critical Error", 
                                 f"The application encountered a critical error:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 