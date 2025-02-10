#!/usr/bin/env python3
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

# Add project root to Python path when run directly
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from src.tabs.directory_tab import DirectoryTab
from src.tabs.single_files_tab import SingleFilesTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Merger")
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(SingleFilesTab(), "Single Files")
        self.tabs.addTab(DirectoryTab(), "Directory")
        
        # Set central widget
        self.setCentralWidget(self.tabs)
        
        # Set initial size
        self.resize(800, 600)

def main():
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 