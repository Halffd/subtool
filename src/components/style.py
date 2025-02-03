"""Style definitions for the application."""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #323232;
    color: #ffffff;
    padding: 8px 20px;
    border: 1px solid #3a3a3a;
}

QTabBar::tab:selected {
    background-color: #404040;
    border-bottom: none;
}

QPushButton {
    background-color: #0d47a1;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #1565c0;
}

QPushButton:pressed {
    background-color: #0a3d91;
}

QPushButton:disabled {
    background-color: #666666;
    color: #aaaaaa;
}

QLineEdit, QTextEdit {
    background-color: #323232;
    color: white;
    border: 1px solid #3a3a3a;
    padding: 5px;
    border-radius: 4px;
}

QProgressBar {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    text-align: center;
    background-color: #323232;
}

QProgressBar::chunk {
    background-color: #0d47a1;
}

QLabel {
    color: white;
}

QListWidget {
    background-color: #323232;
    color: white;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #0d47a1;
}

QScrollBar:vertical {
    border: none;
    background-color: #2b2b2b;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #2b2b2b;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #404040;
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

# Color definitions
COLORS = {
    'WHITE': '#FFFFFF',
    'YELLOW': '#FFFF00',
    'GREEN': '#00FF00',
    'CYAN': '#00FFFF',
    'BLUE': '#0000FF',
    'MAGENTA': '#FF00FF',
    'RED': '#FF0000'
} 