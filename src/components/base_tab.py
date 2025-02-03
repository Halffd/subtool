"""Base tab component with common functionality."""

from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QTextEdit)
from PyQt6.QtCore import Qt
import logging

from .style import DARK_THEME
from .sync_controls import SyncControls
from ..utils.settings import Settings
from ..utils.logger import setup_logger, QTextEditLogger

class BaseTab(QWidget):
    """Base class for tabs with common functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create config directory in the application folder
        self.config_dir = Path(__file__).parent.parent.parent / 'conf'
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize settings
        self.settings_manager = Settings(self.config_dir)
        
        # Setup logging
        self.logger = setup_logger('SubtitleMerger', self.config_dir / 'subtitle_merger.log')
        
        # Set style sheet
        self.setStyleSheet(DARK_THEME)
        
        # Create main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # Create content widget and its layout
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        
        # Create sync controls
        self.sync_controls = SyncControls(self, self.settings_manager, self.logger)
        
        # Enable focus for key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Setup UI
        self.setup_ui()
        
        # Setup log section
        self.setup_log_section()

    def setup_ui(self):
        """Setup the base UI elements. Override in subclasses."""
        pass

    def setup_log_section(self):
        """Setup the log section."""
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Logs will appear here...")
        
        # Add text widget handler
        text_handler = QTextEditLogger(self.log_text)
        text_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(text_handler)
        
        self.layout.addWidget(self.log_text)

    def save_settings(self, settings=None):
        """Save current settings."""
        self.settings_manager.save(settings)

    def get_settings(self, key, default=None):
        """Get a setting value."""
        return self.settings_manager.get(key, default)

    def set_setting(self, key, value):
        """Set a setting value."""
        self.settings_manager.set(key, value) 