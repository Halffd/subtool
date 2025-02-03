"""Base tab component with common functionality."""

from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QTextEdit, QLabel
from PyQt6.QtCore import Qt
import logging

from src.components.style import DARK_THEME
from src.utils.logger import setup_logger, QTextEditLogger

class BaseTab(QWidget):
    """Base class for tabs with common functionality."""
    
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        
        # Setup logging
        self.logger = setup_logger(f"srtmerger.{name}")
        
        # Set style sheet
        self.setStyleSheet(DARK_THEME)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setLayout(main_layout)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(scroll)
        
        # Create content widget and its layout
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(10)  # Add spacing between widgets
        self.layout.setContentsMargins(10, 10, 10, 10)  # Add padding
        scroll.setWidget(content_widget)
        
        # Enable focus for key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Setup log section
        self.setup_log_section()

    def setup_log_section(self):
        """Setup the log section."""
        self.layout.addWidget(QLabel("Log:"))
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Logs will appear here...")
        self.log_text.setMinimumHeight(100)  # Ensure log section is visible
        
        # Add text widget handler
        text_handler = QTextEditLogger(self)
        text_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(text_handler)
        
        self.layout.addWidget(self.log_text)

    def get_log_widget(self):
        """Get the log widget for this tab."""
        return self.log_text 