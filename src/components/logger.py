"""Logging components for the application."""

import logging
from PyQt6.QtWidgets import QTextEdit
import sys

class QTextEditLogger(logging.Handler):
    """Custom logging handler that writes to a QTextEdit widget."""
    def __init__(self, widget: QTextEdit):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.widget.append(msg)
        except Exception as e:
            print(f"Error writing to log widget: {e}", file=sys.stderr)

def setup_logger(name: str, log_file: str = None, level=logging.DEBUG) -> logging.Logger:
    """Setup and return a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error setting up file handler: {e}", file=sys.stderr)
    
    return logger 