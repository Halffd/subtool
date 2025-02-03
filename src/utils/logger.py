"""Logging utilities for the application."""

import logging
import atexit
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal, QObject

class QTextEditLogger(logging.Handler, QObject):
    """Custom logging handler that writes to a QTextEdit widget."""
    
    new_record = pyqtSignal(str)
    
    def __init__(self, parent=None):
        logging.Handler.__init__(self)
        QObject.__init__(self, parent)
        
        if isinstance(parent, QTextEdit):
            self.widget = parent
        else:
            self.widget = QTextEdit(parent)
            self.widget.setReadOnly(True)
            self.widget.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3a3a3a;
                    font-family: monospace;
                }
            """)
        self.new_record.connect(self.widget.append)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def emit(self, record):
        """Emit a log record."""
        try:
            msg = self.format(record)
            # Add color based on log level
            if record.levelno >= logging.ERROR:
                msg = f'<span style="color: #ff5555;">{msg}</span>'
            elif record.levelno >= logging.WARNING:
                msg = f'<span style="color: #ffb86c;">{msg}</span>'
            elif record.levelno >= logging.INFO:
                msg = f'<span style="color: #50fa7b;">{msg}</span>'
            else:
                msg = f'<span style="color: #6272a4;">{msg}</span>'
            self.new_record.emit(msg)
        except Exception:
            self.handleError(record)
    
    def cleanup(self):
        """Clean up resources before deletion."""
        try:
            # Disconnect signal
            try:
                self.new_record.disconnect()
            except TypeError:
                pass  # Signal was not connected
            
            # Remove handler from all loggers
            for logger in logging.Logger.manager.loggerDict.values():
                if isinstance(logger, logging.Logger):
                    logger.removeHandler(self)
            
            # Clear widget reference
            self.widget = None
        except Exception:
            pass  # Ignore cleanup errors
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Set up a logger with the given name and level.
    
    Args:
        name: Name of the logger
        level: Logging level (default: INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter and add it to the handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger if it doesn't already have it
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger 