#!/usr/bin/env python3
"""Subtitle Merger Tool - Main Entry Point."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox
from PyQt6.QtCore import Qt

from src.components.style import DARK_THEME
from src.tabs.single_files_tab import SingleFilesTab
from src.tabs.directory_tab import DirectoryTab

class SubtitleMergerGUI(QMainWindow):
    """Main application window for the Subtitle Merger GUI."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Subtitle Merger")
        self.setStyleSheet(DARK_THEME)
        
        # Set to fullscreen by default
        self.showMaximized()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Add tabs
        self.single_files_tab = SingleFilesTab(self)
        self.directory_tab = DirectoryTab(self)
        
        tab_widget.addTab(self.single_files_tab, "Single Files")
        tab_widget.addTab(self.directory_tab, "Directory")

    def closeEvent(self, event):
        """Handle application closure."""
        # Check both tabs for running workers
        for tab in [self.single_files_tab, self.directory_tab]:
            if hasattr(tab, 'merge_worker') and tab.merge_worker and tab.merge_worker.isRunning():
                reply = QMessageBox.question(
                    self,
                    'Confirm Exit',
                    'A merge operation is in progress. Do you want to stop it and exit?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    tab.merge_worker.stop()
                    tab.merge_worker.wait()
                else:
                    event.ignore()
                    return
        
        event.accept()

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application-wide dark theme
    app.setStyle("Fusion")  # Use Fusion style for better dark theme support
    
    window = SubtitleMergerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 