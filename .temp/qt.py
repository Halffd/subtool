#!/usr/bin/env python3
import sys
import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QTextEdit, QFileDialog, QFrame, 
                            QGroupBox, QCheckBox, QTabWidget, QSlider,
                            QSpinBox, QGridLayout, QMessageBox, QColorDialog,
                            QScrollArea, QScrollBar, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QThread, QEvent
from PyQt6.QtGui import QRegularExpressionValidator, QTextCursor
from main import Merger
import json
import shutil
import subprocess

WHITE = '#FFFFFF'
BLUE = '#0000FF'
YELLOW = '#FFFF00'

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

@dataclass
class EpisodeMatch:
    """Data class for storing matched episode files."""
    episode_num: int
    sub1_path: Path
    sub2_path: Path
    output_path: Optional[Path] = None

class QTextEditLogger(logging.Handler):
    """Custom logging handler that writes to a QTextEdit widget."""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.widget.append(msg)
        except Exception as e:
            print(f"Error writing to log widget: {e}", file=sys.stderr)

class MergeWorker(QThread):
    """Worker thread for handling subtitle merging operations."""
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, matches: List[EpisodeMatch], merger_args: Dict[str, Any]):
        super().__init__()
        self.matches = matches
        self.merger_args = merger_args
        self.is_running = True

    def run(self):
        try:
            for match in self.matches:
                if not self.is_running:
                    break
                
                try:
                    self.progress.emit(f"Processing episode {match.episode_num}")
                    
                    # Create merger instance
                    merger = Merger(output_name=str(match.output_path))
                    
                    # Add subtitles
                    merger.add(str(match.sub1_path), 
                             color=self.merger_args['color'],
                             codec=self.merger_args['codec'])
                    merger.add(str(match.sub2_path))
                    
                    # Merge subtitles
                    merger.merge()
                    
                    self.progress.emit(
                        f"Successfully merged episode {match.episode_num} to: {match.output_path}"
                    )
                
                except Exception as e:
                    self.error.emit(f"Error merging episode {match.episode_num}: {str(e)}")
                    continue
                
        except Exception as e:
            self.error.emit(f"Critical error in merge worker: {str(e)}")
        
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False

class EpisodeRangeSelector(QWidget):
    """Widget for selecting episode ranges."""
    range_changed = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Episode range group
        range_group = QGroupBox("Episode Range")
        range_layout = QVBoxLayout()
        
        # Enable/disable range selection
        self.enable_range = QCheckBox("Enable Episode Range")
        range_layout.addWidget(self.enable_range)
        
        # Controls layout
        controls_layout = QGridLayout()
        
        # Spinboxes
        self.start_spin = QSpinBox()
        self.end_spin = QSpinBox()
        for spin in (self.start_spin, self.end_spin):
            spin.setRange(1, 9999)
            spin.setSingleStep(1)
        
        self.end_spin.setValue(9999)
        
        controls_layout.addWidget(QLabel("Start:"), 0, 0)
        controls_layout.addWidget(self.start_spin, 0, 1)
        controls_layout.addWidget(QLabel("End:"), 0, 2)
        controls_layout.addWidget(self.end_spin, 0, 3)
        
        # Sliders
        self.range_slider = QWidget()
        slider_layout = QHBoxLayout(self.range_slider)
        
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        
        for slider in (self.start_slider, self.end_slider):
            slider.setRange(1, 9999)
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            slider.setTickInterval(100)
            slider_layout.addWidget(slider)
        
        self.end_slider.setValue(9999)
        controls_layout.addWidget(self.range_slider, 1, 0, 1, 4)
        
        range_layout.addLayout(controls_layout)
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)
        
        # Initial state
        self.toggle_range_controls(False)
        self.enable_range.setChecked(False)

    def connect_signals(self):
        """Connect all widget signals."""
        self.enable_range.toggled.connect(self.toggle_range_controls)
        self.start_spin.valueChanged.connect(self.start_slider.setValue)
        self.end_spin.valueChanged.connect(self.end_slider.setValue)
        self.start_slider.valueChanged.connect(self.start_spin.setValue)
        self.end_slider.valueChanged.connect(self.end_spin.setValue)
        
        # Connect range changed signals
        for widget in (self.start_spin, self.end_spin):
            widget.valueChanged.connect(self.emit_range_changed)

    def toggle_range_controls(self, enabled: bool):
        """Enable or disable range selection controls."""
        for widget in (self.start_spin, self.end_spin, self.range_slider):
            widget.setEnabled(enabled)
        if enabled:
            self.emit_range_changed()

    def emit_range_changed(self):
        """Emit the range_changed signal with current values."""
        if self.enable_range.isChecked():
            self.range_changed.emit((self.start_spin.value(), self.end_spin.value()))
        else:
            self.range_changed.emit(None)

    def get_range(self) -> Optional[Tuple[int, int]]:
        """Get the current episode range if enabled."""
        return (
            (self.start_spin.value(), self.end_spin.value())
            if self.enable_range.isChecked() else None
        )

class BaseTab(QWidget):
    """Base class for tabs with common functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create config directory in the application folder
        self.config_dir = Path(__file__).parent / 'conf'
        self.config_dir.mkdir(exist_ok=True)
        
        # Define settings and log file paths
        self.settings_file = self.config_dir / 'configs.json'
        self.log_file = self.config_dir / 'subtitle_merger.log'
        
        # Setup logging first
        self.setup_logging()
        self.logger = logging.getLogger('SubtitleMerger')
        
        # Load settings before UI setup
        self.settings = self.load_settings()
        
        # Define default style
        self.default_style = """
            QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-size: 11px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                padding: 2px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #0f3460;
                border: 1px solid #533483;
                padding: 3px 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #533483;
            }
            QGroupBox {
                border: 1px solid #533483;
                margin-top: 0.5em;
                padding-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #533483;
                height: 4px;
                background: #16213e;
            }
            QSlider::handle:horizontal {
                background: #533483;
                width: 12px;
                margin: -4px 0;
            }
            QCheckBox {
                spacing: 3px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                background-color: #16213e;
                border: 1px solid #533483;
            }
            QCheckBox::indicator:checked {
                background-color: #533483;
            }
            QTabWidget::pane {
                border: 1px solid #533483;
                background-color: #1a1a2e;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background-color: #16213e;
                border: 1px solid #533483;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0f3460;
            }
            QTabBar::tab:hover {
                background-color: #533483;
            }
        """
        
        # Initialize UI elements as class attributes
        self.sub1_font_slider = None
        self.sub2_font_slider = None
        self.sub1_font_spinbox = None
        self.sub2_font_spinbox = None
        self.scale_slider = None
        self.scale_input = None
        self.color_combo = None
        self.codec_combo = None
        self.option_merge_subtitles = None
        self.option_generate_log = None
        
        # Set style sheet
        self.setStyleSheet(self.default_style)
        
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
        
        # Enable focus for key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Setup UI after settings are loaded
        self.setup_ui()

    def setup_logging(self):
        """Setup logging configuration."""
        try:
            self.logger = logging.getLogger('SubtitleMerger')
            self.logger.setLevel(logging.DEBUG)
            
            # Create formatters
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
            
            # File handler
            try:
                file_handler = logging.FileHandler(self.log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(file_formatter)
            except Exception as e:
                print(f"Error setting up file handler: {e}", file=sys.stderr)
                file_handler = None
            
            # Console handler (stderr)
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            
            # Clear existing handlers
            self.logger.handlers.clear()
            
            # Add handlers
            if file_handler:
                self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            # Store handlers to add text widget handler later
            self.file_handler = file_handler
            self.console_handler = console_handler
            self.log_formatter = file_formatter
            
        except Exception as e:
            print(f"Error setting up logging: {e}", file=sys.stderr)

    def eventFilter(self, obj, event):
        """Handle scroll events with specific modifiers."""
        if event.type() == QEvent.Type.Wheel:
            modifiers = event.modifiers()
            
            # Block scrollbar scrolling when any modifier is pressed
            if modifiers & (Qt.KeyboardModifier.ControlModifier |
                          Qt.KeyboardModifier.ShiftModifier |
                          Qt.KeyboardModifier.AltModifier |
                          Qt.KeyboardModifier.MetaModifier):
                
                # If Ctrl is pressed, handle scaling
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    delta = event.angleDelta().y()
                    if delta > 0:
                        self.adjust_scale(25)
                        self.logger.debug(f"Scale increased to {self.scale_slider.value()}%")
                    elif delta < 0:
                        self.adjust_scale(-25)
                        self.logger.debug(f"Scale decreased to {self.scale_slider.value()}%")
                
                # If Meta (Win) is pressed and the target is a QComboBox, change its index
                if modifiers & Qt.KeyboardModifier.MetaModifier and isinstance(obj, QComboBox):
                    delta = event.angleDelta().y()
                    current_index = obj.currentIndex()
                    if delta > 0 and current_index > 0:
                        obj.setCurrentIndex(current_index - 1)
                    elif delta < 0 and current_index < obj.count() - 1:
                        obj.setCurrentIndex(current_index + 1)
                
                return True
            
            # Only allow scrolling when the mouse is over the scrollbar
            if isinstance(obj, QScrollBar):
                return False  # Allow the scroll event
            else:
                return True  # Block the scroll event
                
        return super().eventFilter(obj, event)

    def adjust_scale(self, delta: int):
        """Adjust scale by the given delta."""
        new_value = self.scale_slider.value() + delta
        new_value = max(10, min(500, new_value))  # Clamp between 10 and 500
        self.scale_slider.setValue(new_value)
        self.scale_input.setValue(new_value)
        self.update_scale(new_value)
        self.logger.debug(f"Scale adjusted to {new_value}%")

    def on_scale_changed(self, value: int):
        """Handle scale changes from either slider or input."""
        # Update both controls without triggering recursion
        if self.sender() == self.scale_slider:
            self.scale_input.setValue(value)
        else:
            self.scale_slider.setValue(value)
        self.update_scale(value)
        self.logger.debug(f"Scale changed to {value}%")
        self.save_settings()  # Save immediately

    def update_scale(self, value):
        """Update the font scale."""
        scale_factor = value / 100.0
        
        # Get the application instance
        app = QApplication.instance()
        
        # Get the default font
        font = app.font()
        
        # Calculate the new point size
        base_size = 10  # Base font size
        new_size = int(base_size * scale_factor)
        
        # Set the new font size
        font.setPointSize(new_size)
        
        # Apply the font to the application
        app.setFont(font)
        
        # Update stylesheet with new sizes
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #2b2b2b;
                color: #ffffff;
                font-size: {new_size}pt;
            }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                background-color: #3b3b3b;
                border: 1px solid #555555;
                padding: {int(5 * scale_factor)}px;
                font-size: {new_size}pt;
            }}
            QPushButton {{
                background-color: #444444;
                border: 1px solid #555555;
                padding: {int(5 * scale_factor)}px {int(10 * scale_factor)}px;
                font-size: {new_size}pt;
                min-height: {int(25 * scale_factor)}px;
            }}
            QPushButton:hover {{
                background-color: #4f4f4f;
            }}
            QPushButton:pressed {{
                background-color: #353535;
            }}
            QCheckBox {{
                spacing: {int(5 * scale_factor)}px;
                font-size: {new_size}pt;
            }}
            QCheckBox::indicator {{
                width: {int(20 * scale_factor)}px;
                height: {int(20 * scale_factor)}px;
                background-color: #3b3b3b;
                border: 1px solid #555555;
            }}
            QCheckBox::indicator:checked {{
                background-color: #4f4f4f;
                image: url(check.png);
            }}
            QCheckBox::indicator:hover {{
                border-color: #666666;
            }}
            QGroupBox {{
                border: 1px solid #555555;
                margin-top: {int(20 * scale_factor)}px;
                font-size: {new_size}pt;
                padding-top: {int(10 * scale_factor)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {int(10 * scale_factor)}px;
                padding: {int(3 * scale_factor)}px {int(5 * scale_factor)}px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #2b2b2b;
                width: {int(14 * scale_factor)}px;
                margin: {int(15 * scale_factor)}px 0;
            }}
            QScrollBar::handle:vertical {{
                background: #444444;
                min-height: {int(30 * scale_factor)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #4f4f4f;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QLabel {{
                line-height: 130%;
                font-size: {new_size}pt;
            }}
            QComboBox {{
                padding: {int(5 * scale_factor)}px;
                font-size: {new_size}pt;
                min-height: {int(25 * scale_factor)}px;
            }}
            QSpinBox {{
                padding: {int(5 * scale_factor)}px;
                font-size: {new_size}pt;
                min-height: {int(25 * scale_factor)}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {int(20 * scale_factor)}px;
            }}
            QComboBox::down-arrow {{
                width: {int(12 * scale_factor)}px;
                height: {int(12 * scale_factor)}px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: {int(20 * scale_factor)}px;
            }}
        """)

    def setup_dark_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton {
                background-color: #444444;
                border: 1px solid #555555;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4f4f4f;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QGroupBox {
                border: 1px solid #555555;
                margin-top: 1em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 14px;
                margin: 15px 0 15px 0;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QLabel {
                line-height: 130%;
            }
        """)

    def setup_ui(self):
        """Setup the base UI elements common to all tabs."""
        # Scale selection (moved to top)
        self.setup_scale_selection()
        
        # Add subtitle font size controls
        self.setup_subtitle_sizes()
        
        # Color selection
        self.setup_color_selection()
        
        # Codec selection
        self.setup_codec_selection()
        
        # Options section
        self.setup_options()
        
        # Add stretch to push log section to bottom
        self.layout.addStretch()
        
        # Log section (moved to bottom)
        self.setup_log_section()
        
        # Install event filter on combo boxes
        for combo in self.findChildren(QComboBox):
            combo.installEventFilter(self)

    def setup_scale_selection(self):
        """Setup scale selection group."""
        scale_group = QGroupBox("UI Scale")
        scale_layout = QVBoxLayout()
        scale_layout.setSpacing(10)
        
        # Add description
        description = QLabel("Adjust the size of the text:")
        description.setWordWrap(True)
        scale_layout.addWidget(description)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Decrease button
        decrease_btn = QPushButton("-")
        decrease_btn.setFixedWidth(40)
        decrease_btn.clicked.connect(lambda: self.adjust_scale(-25))
        controls_layout.addWidget(decrease_btn)
        
        # Scale slider
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(500)
        self.scale_slider.setValue(375)  # Default to 375%
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scale_slider.setTickInterval(25)
        controls_layout.addWidget(self.scale_slider)
        
        # Increase button
        increase_btn = QPushButton("+")
        increase_btn.setFixedWidth(40)
        increase_btn.clicked.connect(lambda: self.adjust_scale(25))
        controls_layout.addWidget(increase_btn)
        
        # Scale input
        self.scale_input = QSpinBox()
        self.scale_input.setMinimum(10)
        self.scale_input.setMaximum(500)
        self.scale_input.setValue(375)
        self.scale_input.setSuffix("%")
        self.scale_input.setFixedWidth(70)
        controls_layout.addWidget(self.scale_input)
        
        scale_layout.addLayout(controls_layout)
        scale_group.setLayout(scale_layout)
        
        # Add scale group to the top of the layout
        self.layout.insertWidget(0, scale_group)
        
        # Connect signals
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        self.scale_input.valueChanged.connect(self.on_scale_changed)
        
        # Set initial value from settings
        initial_scale = self.settings.get('ui_scale', 375)
        self.scale_slider.setValue(initial_scale)
        self.scale_input.setValue(initial_scale)
        self.update_scale(initial_scale)

    def setup_subtitle_sizes(self):
        """Setup font size controls for both subtitles."""
        size_group = QGroupBox("Subtitle Font Sizes")
        size_layout = QVBoxLayout()
        
        # Subtitle 1 size
        sub1_size_layout = QHBoxLayout()
        sub1_size_layout.addWidget(QLabel("Subtitle 1 Size:"))
        
        self.sub1_font_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub1_font_slider.setMinimum(8)
        self.sub1_font_slider.setMaximum(52)
        self.sub1_font_slider.setValue(self.settings.get('sub1_font_size', 16))
        self.sub1_font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sub1_font_slider.setTickInterval(4)
        
        self.sub1_font_spinbox = QSpinBox()
        self.sub1_font_spinbox.setMinimum(8)
        self.sub1_font_spinbox.setMaximum(52)
        self.sub1_font_spinbox.setValue(self.settings.get('sub1_font_size', 16))
        self.sub1_font_spinbox.setSuffix("px")
        
        sub1_size_layout.addWidget(self.sub1_font_slider)
        sub1_size_layout.addWidget(self.sub1_font_spinbox)
        size_layout.addLayout(sub1_size_layout)
        
        # Subtitle 2 size
        sub2_size_layout = QHBoxLayout()
        sub2_size_layout.addWidget(QLabel("Subtitle 2 Size:"))
        
        self.sub2_font_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub2_font_slider.setMinimum(8)
        self.sub2_font_slider.setMaximum(52)
        self.sub2_font_slider.setValue(self.settings.get('sub2_font_size', 16))
        self.sub2_font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sub2_font_slider.setTickInterval(4)
        
        self.sub2_font_spinbox = QSpinBox()
        self.sub2_font_spinbox.setMinimum(8)
        self.sub2_font_spinbox.setMaximum(52)
        self.sub2_font_spinbox.setValue(self.settings.get('sub2_font_size', 16))
        self.sub2_font_spinbox.setSuffix("px")
        
        sub2_size_layout.addWidget(self.sub2_font_slider)
        sub2_size_layout.addWidget(self.sub2_font_spinbox)
        size_layout.addLayout(sub2_size_layout)
        
        # Connect signals
        self.sub1_font_slider.valueChanged.connect(self.sub1_font_spinbox.setValue)
        self.sub1_font_spinbox.valueChanged.connect(self.sub1_font_slider.setValue)
        self.sub2_font_slider.valueChanged.connect(self.sub2_font_spinbox.setValue)
        self.sub2_font_spinbox.valueChanged.connect(self.sub2_font_slider.setValue)
        
        # Connect to settings save
        self.sub1_font_slider.valueChanged.connect(lambda v: self.save_value_to_settings('sub1_font_size', v))
        self.sub2_font_slider.valueChanged.connect(lambda v: self.save_value_to_settings('sub2_font_size', v))
        
        size_group.setLayout(size_layout)
        self.layout.addWidget(size_group)

    def setup_color_selection(self):
        """Setup color selection group."""
        color_group = QGroupBox("Color Selection")
        color_layout = QVBoxLayout()
        
        # Add description
        description = QLabel("Select the color for the first subtitle track:")
        description.setWordWrap(True)
        color_layout.addWidget(description)
        
        # Color selection row
        color_row = QHBoxLayout()
        
        # Color combo
        self.color_combo = QComboBox()
        self.color_combo.addItems([
            "Yellow", "White", "Blue"  # Changed order to make Yellow default
        ])
        self.color_combo.currentTextChanged.connect(self.update_color_preview)
        color_row.addWidget(self.color_combo)
        
        # Color picker button with fixed width
        color_picker_btn = QPushButton("...")
        color_picker_btn.setFixedWidth(40)
        color_picker_btn.setToolTip("Open custom color picker")
        color_picker_btn.clicked.connect(self.on_color_picker_clicked)
        color_row.addWidget(color_picker_btn)
        
        # Color preview label
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        color_row.addWidget(self.color_preview)
        
        color_layout.addLayout(color_row)
        color_group.setLayout(color_layout)
        self.layout.addWidget(color_group)
        
        # Set initial color from settings
        initial_color = self.settings.get('color', 'Yellow')
        index = self.color_combo.findText(initial_color)
        if index >= 0:
            self.color_combo.setCurrentIndex(index)
        self.update_color_preview(initial_color)

        # Connect color change to save settings
        self.color_combo.currentTextChanged.connect(self.save_value_to_settings)

    def setup_codec_selection(self):
        """Setup codec selection."""
        codec_group = QGroupBox("Subtitle Encoding")
        codec_layout = QVBoxLayout()
        
        # Add description
        description = QLabel("Select the encoding for the subtitle files:")
        description.setWordWrap(True)
        codec_layout.addWidget(description)
        
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["UTF-8", "Windows-1252"])
        
        codec_layout.addWidget(self.codec_combo)
        codec_group.setLayout(codec_layout)
        self.layout.addWidget(codec_group)
        
        # Set initial codec from settings
        initial_codec = self.settings.get('codec', 'UTF-8')
        index = self.codec_combo.findText(initial_codec)
        if index >= 0:
            self.codec_combo.setCurrentIndex(index)

        # Connect codec change to save settings
        self.codec_combo.currentTextChanged.connect(self.save_value_to_settings)

    def setup_options(self):
        """Setup options section."""
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.option_merge_subtitles = QCheckBox("Merge Subtitles Automatically")
        self.option_merge_subtitles.setChecked(
            self.settings.get('merge_automatically', True)
        )
        self.option_merge_subtitles.stateChanged.connect(self.save_value_to_settings)
        
        self.option_generate_log = QCheckBox("Generate Log File")
        self.option_generate_log.setChecked(
            self.settings.get('generate_log', False)
        )
        self.option_generate_log.stateChanged.connect(self.save_value_to_settings)
        
        options_layout.addWidget(self.option_merge_subtitles)
        options_layout.addWidget(self.option_generate_log)
        
        options_group.setLayout(options_layout)
        self.layout.addWidget(options_group)

    def setup_log_section(self):
        """Setup log section."""
        # Define QTextEditHandler class
        class QTextEditHandler(logging.Handler):
            """Custom logging handler that writes to a QTextEdit widget."""
            def __init__(self, widget):
                super().__init__()
                self.widget = widget

            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.widget.append(msg)
                except Exception as e:
                    print(f"Error writing to log widget: {e}", file=sys.stderr)

        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Logs will appear here...")
        
        # Add text widget handler
        text_handler = QTextEditHandler(self.log_text)
        text_handler.setFormatter(self.log_formatter)
        self.logger.addHandler(text_handler)

        clear_log_button = QPushButton("Clear Logs")
        clear_log_button.clicked.connect(self.clear_logs)

        log_layout.addWidget(self.log_text)
        log_layout.addWidget(clear_log_button)

        log_group.setLayout(log_layout)
        self.layout.addWidget(log_group)
    
    def on_color_picker_clicked(self):
        """Handle custom color picker."""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name().upper()
            self.color_combo.addItem(hex_color)
            self.color_combo.setCurrentText(hex_color)
            self.update_color_preview(hex_color)
            self.logger.info(f"Custom color selected: {hex_color}")
            self.save_settings()  # Save immediately
    
    def update_color_preview(self, color_name: str):
        """Update the color preview label."""
        # Convert common color names to hex
        color_map = {
            "White": "#FFFFFF",
            "Yellow": "#FFFF00",
            "Blue": "#0000FF"
        }
        
        # Get hex color value
        color_hex = color_map.get(color_name, color_name)
        
        # Update preview
        self.color_preview.setStyleSheet(
            f"background-color: {color_hex}; border: 1px solid black;"
        )
    
    def clear_logs(self):
        """Clear both the log text area and optionally the log file."""
        self.log_text.clear()
    
    def get_merger_args(self):
        """Get common merger arguments."""
        # Convert color names to hex values
        color_map = {
            "White": "#FFFFFF",
            "Yellow": "#FFFF00",
            "Blue": "#0000FF"
        }
        color = self.color_combo.currentText()
        color_hex = color_map.get(color, color)
        
        return {
            'color': color_hex,
            'codec': self.codec_combo.currentText()
        }

    def load_settings(self) -> dict:
        """Load settings from JSON file."""
        default_settings = {
            'ui_scale': 275,
            'sub1_font_size': 16,
            'sub2_font_size': 16,
            'color': 'Yellow',
            'codec': 'UTF-8',
            'merge_automatically': True,
            'generate_log': False,
            'last_directory': str(Path.home()),
            'last_video_directory': str(Path.home()),
            'last_subtitle_directory': str(Path.home()),
            'sub1_pattern': r'\[Some-Stuffs\]_Pocket_Monsters_\(2019\)_\d+.*(?<!Clean)\.srt$',  # Match base subtitles without Clean
            'sub2_pattern': r'\[Some-Stuffs\]_Pocket_Monsters_\(2019\)_\d+.*-Clean\.srt$',  # Match files ending with Clean.srt
            'sub1_episode_pattern': r'_(\d{3})_',  # Match episode numbers between underscores
            'sub2_episode_pattern': r'_(\d{3})_',  # Match episode numbers between underscores
            'episode_pattern': r'\d+'  # Legacy support
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.logger.debug("Settings loaded successfully")
                    # Merge with defaults in case new settings were added
                    return {**default_settings, **settings}
            else:
                self.logger.info("No settings file found, creating with defaults")
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4)
                return default_settings
                
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            return default_settings

    def save_settings(self, settings=None):
        """Save current settings to JSON file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)
            
            if settings:
                # Update settings with provided values
                self.settings.update(settings)
            else:
                # Only save values for attributes that exist
                if hasattr(self, 'scale_slider'):
                    self.settings['ui_scale'] = self.scale_slider.value()
                if hasattr(self, 'sub1_font_slider'):
                    self.settings['sub1_font_size'] = self.sub1_font_slider.value()
                if hasattr(self, 'sub2_font_slider'):
                    self.settings['sub2_font_size'] = self.sub2_font_slider.value()
                if hasattr(self, 'color_combo'):
                    self.settings['color'] = self.color_combo.currentText()
                if hasattr(self, 'codec_combo'):
                    self.settings['codec'] = self.codec_combo.currentText()
                if hasattr(self, 'option_merge_subtitles'):
                    self.settings['merge_automatically'] = self.option_merge_subtitles.isChecked()
                if hasattr(self, 'option_generate_log'):
                    self.settings['generate_log'] = self.option_generate_log.isChecked()
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.debug("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def save_value_to_settings(self, key: str, value: str):
        """Save a specific value to settings."""
        try:
            self.settings[key] = value
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.debug(f"Saved {key} to settings")
        except Exception as e:
            self.logger.error(f"Error saving {key} to settings: {e}")

    def save_all_values(self):
        """Save all current values to settings file."""
        try:
            # Update all settings
            settings_update = {
                # UI Scale
                'ui_scale': self.scale_slider.value() if hasattr(self, 'scale_slider') else 375,
                
                # Font sizes
                'sub1_font_size': self.sub1_font_slider.value() if hasattr(self, 'sub1_font_slider') else 16,
                'sub2_font_size': self.sub2_font_slider.value() if hasattr(self, 'sub2_font_slider') else 16,
                
                # Colors and codec
                'color': self.color_combo.currentText() if hasattr(self, 'color_combo') else 'Yellow',
                'codec': self.codec_combo.currentText() if hasattr(self, 'codec_combo') else 'UTF-8',
                
                # Options
                'merge_automatically': self.option_merge_subtitles.isChecked() if hasattr(self, 'option_merge_subtitles') else True,
                'generate_log': self.option_generate_log.isChecked() if hasattr(self, 'option_generate_log') else False,
            }
            
            # Add directory-specific settings if they exist
            if hasattr(self, 'dir_entry'):
                settings_update.update({
                    'last_subtitle_directory': self.dir_entry.text() or str(Path.home()),
                    'last_directory': str(Path(self.dir_entry.text()).parent) if self.dir_entry.text() else str(Path.home())
                })
            
            if hasattr(self, 'video_dir_entry'):
                settings_update['last_video_directory'] = str(Path(self.video_dir_entry.text()).parent) if self.video_dir_entry.text() else str(Path.home())
            
            # Update settings and save
            self.settings.update(settings_update)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.debug("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def test_patterns(self):
        """Test the current patterns against files in the selected directory."""
        input_dir = self.dir_entry.text()
        if not input_dir:
            self.logger.error("Please select an input directory first")
            return

        try:
            input_path = Path(input_dir)
            
            # Get current patterns from UI
            sub1_pattern = self.sub1_pattern_entry.text()
            sub2_pattern = self.sub2_pattern_entry.text()
            sub1_ep_pattern = self.sub1_episode_pattern_entry.text()
            sub2_ep_pattern = self.sub2_episode_pattern_entry.text()
            
            # Find matching files
            sub1_files = [f for f in input_path.glob('*.srt') 
                         if re.search(sub1_pattern, f.name, re.IGNORECASE)]
            sub2_files = [f for f in input_path.glob('*.srt')
                         if re.search(sub2_pattern, f.name, re.IGNORECASE)]
            self.logger.debug('Sub 1', sub1_files)
            self.logger.debug('Sub 2', sub2_files)
            # Test episode number extraction
            sub1_episodes = []
            sub2_episodes = []
            
            for f in sub1_files[:5]:  # Test first 5 files
                match = re.search(sub1_ep_pattern, f.stem)
                if match:
                    sub1_episodes.append((f.name, match.group(1)))
                    
            for f in sub2_files[:5]:  # Test first 5 files
                match = re.search(sub2_ep_pattern, f.stem)
                if match:
                    sub2_episodes.append((f.name, match.group(1)))
            
            # Show results
            msg = QMessageBox()
            msg.setWindowTitle("Pattern Test Results")
            
            results = [
                f"Sub1 Pattern ({sub1_pattern}):",
                f"Found {len(sub1_files)} matching files",
                "\nExample matches with episode numbers:",
                *[f"{name} -> Episode {ep}" for name, ep in sub1_episodes],
                "\nSub2 Pattern ({sub2_pattern}):",
                f"Found {len(sub2_files)} matching files",
                "\nExample matches with episode numbers:",
                *[f"{name} -> Episode {ep}" for name, ep in sub2_episodes]
            ]
            
            msg.setText("\n".join(results))
            msg.exec()
            
        except re.error as e:
            self.logger.error(f"Invalid regular expression: {e}")
            QMessageBox.critical(self, "Error", f"Invalid regular expression: {e}")
        except Exception as e:
            self.logger.error(f"Error testing patterns: {e}")
            QMessageBox.critical(self, "Error", f"Error testing patterns: {e}")

class SingleFilesTab(BaseTab):
    """Tab for processing single files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alass_path = shutil.which('alass') or '/usr/bin/alass'
        
    def setup_ui(self):
        """Setup specific UI for single files tab."""
        super().setup_ui()
        
        main_layout = QHBoxLayout()  # Use horizontal layout for main container
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        
        # File selection group (left panel)
        file_group = QGroupBox("Input Files")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(2)
        
        # First subtitle
        sub1_layout = QHBoxLayout()
        self.sub1_entry = QLineEdit()
        browse_sub1_button = QPushButton("Browse")
        browse_sub1_button.clicked.connect(lambda: self.browse_file(self.sub1_entry, "Select First Subtitle"))
        sub1_layout.addWidget(QLabel("Sub 1:"))
        sub1_layout.addWidget(self.sub1_entry)
        sub1_layout.addWidget(browse_sub1_button)
        
        # Second subtitle
        sub2_layout = QHBoxLayout()
        self.sub2_entry = QLineEdit()
        browse_sub2_button = QPushButton("Browse")
        browse_sub2_button.clicked.connect(lambda: self.browse_file(self.sub2_entry, "Select Second Subtitle"))
        sub2_layout.addWidget(QLabel("Sub 2:"))
        sub2_layout.addWidget(self.sub2_entry)
        sub2_layout.addWidget(browse_sub2_button)
        
        file_layout.addLayout(sub1_layout)
        file_layout.addLayout(sub2_layout)
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)

        # Basic sync controls (left panel)
        sync_group = QGroupBox("Basic Sync")
        sync_layout = QVBoxLayout()
        sync_layout.setSpacing(2)

        # Manual sync controls for both subtitles in a grid
        sync_grid = QGridLayout()
        sync_grid.setSpacing(2)
        
        # Sub 1 sync
        sync_grid.addWidget(QLabel("Sub 1:"), 0, 0)
        self.sub1_sync_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub1_sync_slider.setMinimum(-10000)
        self.sub1_sync_slider.setMaximum(10000)
        self.sub1_sync_spinbox = QSpinBox()
        self.sub1_sync_spinbox.setMinimum(-10000)
        self.sub1_sync_spinbox.setMaximum(10000)
        self.sub1_sync_spinbox.setSuffix(" ms")
        sync_grid.addWidget(self.sub1_sync_slider, 0, 1)
        sync_grid.addWidget(self.sub1_sync_spinbox, 0, 2)
        
        # Sub 2 sync
        sync_grid.addWidget(QLabel("Sub 2:"), 1, 0)
        self.sub2_sync_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub2_sync_slider.setMinimum(-10000)
        self.sub2_sync_slider.setMaximum(10000)
        self.sub2_sync_spinbox = QSpinBox()
        self.sub2_sync_spinbox.setMinimum(-10000)
        self.sub2_sync_spinbox.setMaximum(10000)
        self.sub2_sync_spinbox.setSuffix(" ms")
        sync_grid.addWidget(self.sub2_sync_slider, 1, 1)
        sync_grid.addWidget(self.sub2_sync_spinbox, 1, 2)
        
        sync_layout.addLayout(sync_grid)
        sync_group.setLayout(sync_layout)
        left_panel.addWidget(sync_group)

        # ALASS settings (right panel)
        alass_group = QGroupBox("ALASS Settings")
        alass_layout = QVBoxLayout()
        alass_layout.setSpacing(2)

        # Enable ALASS checkbox
        self.use_alass = QCheckBox("Enable ALASS Auto-sync")
        self.use_alass.setChecked(self.settings.get('use_alass', False))
        alass_layout.addWidget(self.use_alass)

        # Disable FPS guessing checkbox
        self.disable_fps_guessing = QCheckBox("Disable FPS Guessing")
        self.disable_fps_guessing.setChecked(self.settings.get('disable_fps_guessing', False))
        self.disable_fps_guessing.setToolTip("Disable automatic FPS detection")
        alass_layout.addWidget(self.disable_fps_guessing)

        # ALASS parameters grid
        params_grid = QGridLayout()
        params_grid.setSpacing(2)

        # Interval
        params_grid.addWidget(QLabel("Interval:"), 0, 0)
        self.alass_interval = QSpinBox()
        self.alass_interval.setRange(0, 10000)
        self.alass_interval.setValue(self.settings.get('alass_interval', 100))
        self.alass_interval.setSuffix(" ms")
        params_grid.addWidget(self.alass_interval, 0, 1)

        # Split penalty
        params_grid.addWidget(QLabel("Split Penalty:"), 1, 0)
        self.alass_split_penalty = QDoubleSpinBox()
        self.alass_split_penalty.setRange(0, 1000)
        self.alass_split_penalty.setValue(self.settings.get('alass_split_penalty', 10))
        self.alass_split_penalty.setSingleStep(0.1)
        params_grid.addWidget(self.alass_split_penalty, 1, 1)

        # FPS settings
        params_grid.addWidget(QLabel("Sub FPS:"), 2, 0)
        self.alass_sub_fps = QDoubleSpinBox()
        self.alass_sub_fps.setRange(0, 120)
        self.alass_sub_fps.setValue(self.settings.get('alass_sub_fps', 23.976))
        self.alass_sub_fps.setSingleStep(0.001)
        params_grid.addWidget(self.alass_sub_fps, 2, 1)

        params_grid.addWidget(QLabel("Ref FPS:"), 3, 0)
        self.alass_ref_fps = QDoubleSpinBox()
        self.alass_ref_fps.setRange(0, 120)
        self.alass_ref_fps.setValue(self.settings.get('alass_ref_fps', 23.976))
        self.alass_ref_fps.setSingleStep(0.001)
        params_grid.addWidget(self.alass_ref_fps, 3, 1)

        alass_layout.addLayout(params_grid)
        alass_group.setLayout(alass_layout)
        right_panel.addWidget(alass_group)

        # Add panels to main layout
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=1)
        
        # Merge button at the bottom
        self.merge_button = QPushButton("Merge Subtitles")
        self.merge_button.clicked.connect(self.merge_subtitles)
        self.merge_button.setMinimumHeight(30)
        
        # Final layout assembly
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addLayout(main_layout)
        container_layout.addWidget(self.merge_button)
        container.setLayout(container_layout)
        self.layout.insertWidget(0, container)

        # Connect sync control signals
        self.sub1_sync_slider.valueChanged.connect(self.sub1_sync_spinbox.setValue)
        self.sub1_sync_spinbox.valueChanged.connect(self.sub1_sync_slider.setValue)
        self.sub2_sync_slider.valueChanged.connect(self.sub2_sync_spinbox.setValue)
        self.sub2_sync_spinbox.valueChanged.connect(self.sub2_sync_slider.setValue)

    def sync_subtitle_with_alass(self, video_path: str, subtitle_path: str) -> str:
        """Synchronize subtitle with ALASS using the video as reference."""
        try:
            if not os.path.exists(self.alass_path):
                self.logger.error(f"ALASS not found at {self.alass_path}")
                return subtitle_path

            # Create temporary file for synced subtitle
            temp_dir = Path(subtitle_path).parent
            synced_path = temp_dir / f"synced_{Path(subtitle_path).name}"

            # Build ALASS command with parameters
            cmd = [
                self.alass_path,
                "--interval", str(self.alass_interval.value()),
                "--split-penalty", str(self.alass_split_penalty.value()),
                "--sub-fps-inc", str(self.alass_sub_fps.value()),
                "--sub-fps-ref", str(self.alass_ref_fps.value())
            ]

            # Add disable-fps-guessing if checked
            if self.disable_fps_guessing.isChecked():
                cmd.append("--disable-fps-guessing")

            # Add input/output files
            cmd.extend([video_path, subtitle_path, str(synced_path)])
            
            self.logger.debug(f"Running ALASS command: {' '.join(cmd)}")
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                self.logger.error(f"ALASS sync failed: {process.stderr}")
                return subtitle_path
                
            self.logger.info(f"ALASS sync successful, output saved to {synced_path}")
            return str(synced_path)
            
        except Exception as e:
            self.logger.error(f"Error during ALASS sync: {e}")
            return subtitle_path

    def merge_subtitles(self):
        """Merge the subtitle files."""
        # Save all current values before merging
        self.save_all_values()
        
        sub1_file = self.sub1_entry.text()
        sub2_file = self.sub2_entry.text()
        
        if not all([sub1_file, sub2_file]):
            self.logger.error("Please select all required files")
            return
        
        try:
            # Get color and font sizes
            sub1_color = self.color_combo.currentText()
            sub1_size = self.sub1_font_slider.value()
            sub2_size = self.sub2_font_slider.value()
            
            self.logger.debug(f"Styles - Sub1: color={sub1_color}, size={sub1_size}, Sub2: size={sub2_size}")
            
            # Create output path
            output_path = Path(sub1_file).parent
            base_name = Path(sub1_file).stem

            # Process subtitle 1 with ALASS if enabled
            if self.use_alass.isChecked():
                # Ask for video file
                video_file, _ = QFileDialog.getOpenFileName(
                    self, "Select Reference Video", "", "Video Files (*.mkv *.mp4);;All Files (*)"
                )
                if video_file:
                    sub1_file = self.sync_subtitle_with_alass(video_file, sub1_file)
            
            # Create merger instance
            merger = Merger(
                output_path=str(output_path),
                output_name=f'{base_name}_merged.srt',
                output_encoding=self.codec_combo.currentText()
            )
            
            # Add first subtitle with color, size and sync delay
            merger.add(
                sub1_file,
                codec=self.codec_combo.currentText(),
                color=sub1_color,
                size=sub1_size,
                time_offset=self.sub1_sync_spinbox.value()
            )
            
            # Add second subtitle with size and sync delay
            merger.add(
                sub2_file,
                codec=self.codec_combo.currentText(),
                color=COLORS['WHITE'],
                size=sub2_size,
                time_offset=self.sub2_sync_spinbox.value()
            )
            
            merger.merge()
            self.logger.info(f"Successfully merged subtitles to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error during merge operation: {e}")

    def browse_file(self, entry: QLineEdit, title: str):
        """Browse for a subtitle file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, title, "", "Subtitle Files (*.srt);;All Files (*)"
        )
        if file_path:
            entry.setText(file_path)

class DirectoryTab(BaseTab):
    """Tab for processing directories."""
    
    def __init__(self, parent=None):
        # Call parent init first
        super().__init__(parent)
        
        # Initialize UI elements specific to DirectoryTab
        self.dir_entry = None
        self.video_dir_entry = None
        self.sub1_pattern_entry = None
        self.sub2_pattern_entry = None
        self.sub1_episode_pattern_entry = None
        self.sub2_episode_pattern_entry = None
        self.batch_merge_button = None
        
        # Setup UI
        self.setup_directory_ui()

    def _create_directory_entry(self, label: str, setting_key: str, browse_text: str, browse_func) -> tuple[QHBoxLayout, QLineEdit]:
        """Helper to create a directory entry layout."""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        
        entry = QLineEdit()
        entry.setText(self.settings.get(setting_key, ''))
        entry.textChanged.connect(self.save_directory_settings)
        layout.addWidget(entry)
        
        browse_btn = QPushButton(browse_text)
        browse_btn.clicked.connect(browse_func)
        layout.addWidget(browse_btn)
        
        return layout, entry

    def _create_pattern_entry(self, label: str, setting_key: str, tooltip: str) -> tuple[QHBoxLayout, QLineEdit]:
        """Helper to create a pattern entry layout."""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        
        entry = QLineEdit()
        entry.setText(self.settings.get(setting_key, ''))
        entry.setToolTip(tooltip)
        entry.textChanged.connect(self.save_pattern_settings)
        layout.addWidget(entry)
        
        return layout, entry

    def setup_directory_ui(self):
        """Setup directory-specific UI elements."""
        # Directory selection group
        dir_group = QGroupBox("Directory Selection")
        dir_layout = QVBoxLayout()

        # Create directory entries
        input_layout, self.dir_entry = self._create_directory_entry(
            "Subtitles Directory:", 
            'last_subtitle_directory',
            "Browse",
            self.browse_directory
        )
        dir_layout.addLayout(input_layout)

        video_layout, self.video_dir_entry = self._create_directory_entry(
            "Videos Directory:",
            'last_video_directory',
            "Browse",
            self.browse_video_directory
        )
        dir_layout.addLayout(video_layout)
        
        dir_group.setLayout(dir_layout)
        self.layout.addWidget(dir_group)

        # Pattern group
        pattern_group = QGroupBox("File Patterns")
        pattern_layout = QVBoxLayout()

        # Filter patterns section
        filter_layout = QVBoxLayout()
        filter_layout.addWidget(QLabel("Filter Patterns:"))

        # Create pattern entries
        sub1_filter_layout, self.sub1_pattern_entry = self._create_pattern_entry(
            "Sub1:",
            'sub1_pattern',
            "Pattern to identify Sub1 files"
        )
        filter_layout.addLayout(sub1_filter_layout)

        sub2_filter_layout, self.sub2_pattern_entry = self._create_pattern_entry(
            "Sub2:",
            'sub2_pattern',
            "Pattern to identify Sub2 files"
        )
        filter_layout.addLayout(sub2_filter_layout)

        pattern_layout.addLayout(filter_layout)

        # Episode patterns section
        episode_layout = QVBoxLayout()
        episode_layout.addWidget(QLabel("Episode Number Patterns:"))

        sub1_ep_layout, self.sub1_episode_pattern_entry = self._create_pattern_entry(
            "Sub1:",
            'sub1_episode_pattern',
            "Pattern to find episode numbers in Sub1 files"
        )
        episode_layout.addLayout(sub1_ep_layout)

        sub2_ep_layout, self.sub2_episode_pattern_entry = self._create_pattern_entry(
            "Sub2:",
            'sub2_episode_pattern',
            "Pattern to find episode numbers in Sub2 files"
        )
        episode_layout.addLayout(sub2_ep_layout)

        pattern_layout.addLayout(episode_layout)

        # Test patterns button
        test_btn = QPushButton("Test Patterns")
        test_btn.clicked.connect(self.test_patterns)
        pattern_layout.addWidget(test_btn)

        pattern_group.setLayout(pattern_layout)
        self.layout.addWidget(pattern_group)

        # Add merge button
        self.batch_merge_button = QPushButton("Merge Subtitles")
        self.batch_merge_button.clicked.connect(self.merge_subtitles)
        self.batch_merge_button.setMinimumHeight(40)
        self.layout.addWidget(self.batch_merge_button)

        # Add stretch
        self.layout.addStretch()

        # Add log section last
        self.setup_log_section()

    def save_directory_settings(self):
        """Save directory settings when they change."""
        try:
            self.save_settings({
                'last_subtitle_directory': self.dir_entry.text(),
                'last_video_directory': self.video_dir_entry.text()
            })
        except Exception as e:
            self.logger.error(f"Error saving directory settings: {e}")

    def save_pattern_settings(self):
        """Save all pattern settings when they change."""
        try:
            self.save_settings({
                'sub1_pattern': self.sub1_pattern_entry.text(),
                'sub2_pattern': self.sub2_pattern_entry.text(),
                'sub1_episode_pattern': self.sub1_episode_pattern_entry.text(),
                'sub2_episode_pattern': self.sub2_episode_pattern_entry.text()
            })
        except Exception as e:
            self.logger.error(f"Error saving pattern settings: {e}")

    def browse_directory(self):
        """Browse for an input directory."""
        initial_dir = self.settings.get('last_subtitle_directory', str(Path.home()))
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", initial_dir)
        if directory:
            self.dir_entry.setText(directory)
            self.save_directory_settings()

    def browse_video_directory(self):
        """Browse for a video directory."""
        initial_dir = self.settings.get('last_video_directory', str(Path.home()))
        directory = QFileDialog.getExistingDirectory(self, "Select Video Directory", initial_dir)
        if directory:
            self.video_dir_entry.setText(directory)
            self.save_directory_settings()

    def test_patterns(self):
        """Test the current patterns against files in the selected directory."""
        input_dir = self.dir_entry.text()
        if not input_dir:
            self.logger.error("Please select an input directory first")
            return

        try:
            input_path = Path(input_dir)
            
            # Get current patterns from UI
            sub1_pattern = self.sub1_pattern_entry.text()
            sub2_pattern = self.sub2_pattern_entry.text()
            sub1_ep_pattern = self.sub1_episode_pattern_entry.text()
            sub2_ep_pattern = self.sub2_episode_pattern_entry.text()
            
            # Find matching files
            sub1_files = [f for f in input_path.glob('*.srt') 
                         if re.search(sub1_pattern, f.name, re.IGNORECASE)]
            sub2_files = [f for f in input_path.glob('*.srt')
                         if re.search(sub2_pattern, f.name, re.IGNORECASE)]
            
            # Test episode number extraction
            sub1_episodes = []
            sub2_episodes = []
            
            for f in sub1_files[:5]:  # Test first 5 files
                match = re.search(sub1_ep_pattern, f.stem)
                if match:
                    sub1_episodes.append((f.name, match.group(1)))
                    
            for f in sub2_files[:5]:  # Test first 5 files
                match = re.search(sub2_ep_pattern, f.stem)
                if match:
                    sub2_episodes.append((f.name, match.group(1)))
            
            # Show results
            msg = QMessageBox()
            msg.setWindowTitle("Pattern Test Results")
            self.logger.debug('Sub 1', sub1_files)
            self.logger.debug('Sub 2', sub2_files)
            results = [
                f"Sub1 Pattern ({sub1_pattern}):",
                f"Found {len(sub1_files)} matching files",
                "\nExample matches with episode numbers:",
                *[f"{name} -> Episode {ep}" for name, ep in sub1_episodes],
                "\nSub2 Pattern ({sub2_pattern}):",
                f"Found {len(sub2_files)} matching files",
                "\nExample matches with episode numbers:",
                *[f"{name} -> Episode {ep}" for name, ep in sub2_episodes]
            ]
            
            msg.setText("\n".join(results))
            msg.exec()
            
        except re.error as e:
            self.logger.error(f"Invalid regular expression: {e}")
            QMessageBox.critical(self, "Error", f"Invalid regular expression: {e}")
        except Exception as e:
            self.logger.error(f"Error testing patterns: {e}")
            QMessageBox.critical(self, "Error", f"Error testing patterns: {e}")

    def merge_subtitles(self):
        """Merge the subtitle files in directory."""
        try:
            input_dir = self.dir_entry.text().strip()  # Strip whitespace and newlines
            video_dir = self.video_dir_entry.text().strip()  # Strip whitespace and newlines
            
            if not input_dir or not video_dir:
                self.logger.error("Please select both input and video directories")
                return

            self.logger.info("Starting merge operation...")
            self.logger.info(f"Input directory: {input_dir}")
            self.logger.info(f"Video directory: {video_dir}")
            
            # Get patterns from GUI entries
            sub1_pattern = self.sub1_pattern_entry.text()
            sub2_pattern = self.sub2_pattern_entry.text()
            sub1_ep_pattern = self.sub1_episode_pattern_entry.text()
            sub2_ep_pattern = self.sub2_episode_pattern_entry.text()
            
            # Get color and font sizes
            sub1_color = self.color_combo.currentText()
            sub1_size = self.sub1_font_slider.value()
            sub2_size = self.sub2_font_slider.value()
            
            self.logger.debug(f"Using patterns - Sub1: {sub1_pattern}, Sub2: {sub2_pattern}")
            self.logger.debug(f"Episode patterns - Sub1: {sub1_ep_pattern}, Sub2: {sub2_ep_pattern}")
            self.logger.debug(f"Styles - Sub1: color={sub1_color}, size={sub1_size}, Sub2: size={sub2_size}")
            
            # Find subtitle files (case insensitive)
            try:
                input_path = Path(input_dir)
                video_path = Path(video_dir)
                
                # List all srt files for logging
                all_srt_files = list(input_path.glob('*.srt'))
                self.logger.debug(f"Found {len(all_srt_files)} total .srt files")
                for srt_file in all_srt_files:
                    self.logger.debug(f"Found SRT file: {srt_file.name}")
                
                # Filter sub1 files using regex pattern from GUI
                sub1_files = [f for f in all_srt_files 
                            if re.search(sub1_pattern, f.name, re.IGNORECASE)]
                
                # Filter sub2 files using regex pattern from GUI
                sub2_files = [f for f in all_srt_files
                            if re.search(sub2_pattern, f.name, re.IGNORECASE)]
                
                self.logger.info(f"Found {len(sub1_files)} sub1 files and {len(sub2_files)} sub2 files")
                
                # Log matched files
                self.logger.debug("Sub1 matched files:")
                for f in sub1_files:
                    self.logger.debug(f"  - {f.name}")
                self.logger.debug("Sub2 matched files:")
                for f in sub2_files:
                    self.logger.debug(f"  - {f.name}")
                
            except Exception as e:
                self.logger.error(f"Error finding subtitle files: {e}")
                return

            # Create episode pairs dictionary
            episode_subs = {}
            
            # Process sub1 files
            for sub1 in sub1_files:
                try:
                    ep_match = re.search(sub1_ep_pattern, sub1.stem)
                    self.logger.debug(f"{ep_match} - {sub1}")
                    if ep_match:
                        ep_num = ep_match.group(1)
                        if ep_num not in episode_subs:
                            episode_subs[ep_num] = {'sub1': sub1}
                            self.logger.debug(f"Found sub1 for episode {ep_num}: {sub1.name}")
                        else:
                            self.logger.warning(f"Duplicate sub1 for episode {ep_num}: {sub1.name}")
                    else:
                        self.logger.warning(f"Could not extract episode number from sub1 file: {sub1.name}")
                except Exception as e:
                    self.logger.error(f"Error processing sub1 file {sub1}: {e}")
            
            # Process sub2 files
            for sub2 in sub2_files:
                try:
                    ep_match = re.search(sub2_ep_pattern, sub2.stem)
                    self.logger.debug(f"{ep_match} - {sub2}")
                    if ep_match:
                        ep_num = ep_match.group(1)
                        if ep_num in episode_subs:
                            episode_subs[ep_num]['sub2'] = sub2
                            self.logger.debug(f"Found sub2 for episode {ep_num}: {sub2.name}")
                        else:
                            self.logger.warning(f"Found sub2 but no sub1 for episode {ep_num}: {sub2.name}")
                    else:
                        self.logger.warning(f"Could not extract episode number from sub2 file: {sub2.name}")
                except Exception as e:
                    self.logger.error(f"Error processing sub2 file {sub2}: {e}")

            # Log episode pairs
            self.logger.debug("Episode pairs found:")
            for ep_num, subs in episode_subs.items():
                sub1_name = subs.get('sub1', 'missing').name if 'sub1' in subs else 'missing'
                sub2_name = subs.get('sub2', 'missing').name if 'sub2' in subs else 'missing'
                self.logger.debug(f"Episode {ep_num}: sub1={sub1_name}, sub2={sub2_name}")

            # Find and process video files - only look for MKV files
            video_files = [f for f in Path(video_dir).glob('**/*.mkv')]
            
            self.logger.info(f"Found {len(video_files)} video files")

            # Process each video file
            for video_file in video_files:
                self.logger.debug(f"Found video file: {video_file.name}")
                try:
                    # Extract episode number using the sub2 episode pattern
                    match = re.search(sub2_ep_pattern, video_file.stem)
                    if not match:
                        match = re.search(r'(\d+)', video_file.stem)
                        if not match:
                            self.logger.warning(f"Could not find episode number in {video_file.name}")
                            continue
                    
                    ep_num = match.group(1)  # Get the episode number
                    self.logger.debug(f"Extracted episode number {ep_num} from {video_file.name}")
                    
                    if ep_num not in episode_subs:
                        self.logger.warning(f"No subtitles found for episode {ep_num}")
                        continue
                    if 'sub2' not in episode_subs[ep_num]:
                        self.logger.warning(f"Missing sub2 for episode {ep_num}")
                        continue
                    
                    sub1_file = episode_subs[ep_num]['sub1']
                    sub2_file = episode_subs[ep_num]['sub2']
                    self.logger.debug(f"Processing episode {ep_num} with sub1={sub1_file.name}, sub2={sub2_file.name}")
                    
                    # Copy subtitle files next to video with consistent naming
                    try:
                        sub1_dest = video_file.parent / f'{video_file.stem}.sub1.srt'
                        sub2_dest = video_file.parent / f'{video_file.stem}.sub2.srt'
                        shutil.copy2(sub1_file, sub1_dest)
                        shutil.copy2(sub2_file, sub2_dest)
                        self.logger.info(f"Copied subtitle files for episode {ep_num}")
                        self.logger.debug(f"  - {sub1_file.name} -> {sub1_dest.name}")
                        self.logger.debug(f"  - {sub2_file.name} -> {sub2_dest.name}")
                    except Exception as e:
                        self.logger.error(f"Error copying subtitle files for episode {ep_num}: {e}")
                        continue
                    
                    # Create merger instance and merge
                    try:
                        output_name = f'{video_file.stem}.merged.srt'
                        self.logger.debug(f"Creating merger for episode {ep_num}, output={output_name}")
                        merger = Merger(
                            output_path=str(video_file.parent),
                            output_name=output_name,
                            output_encoding=self.codec_combo.currentText()
                        )
                        
                        # Add first subtitle with color and size
                        self.logger.debug(f"Adding sub1 with color={sub1_color}, size={sub1_size}")
                        merger.add(
                            str(sub1_file),
                            codec=self.codec_combo.currentText(),
                            color=sub1_color,
                            size=sub1_size,
                            #top=False
                        )
                        
                        # Add second subtitle with size
                        self.logger.debug(f"Adding sub2 with size={sub2_size}")
                        merger.add(
                            str(sub2_file),
                            codec=self.codec_combo.currentText(),
                            color=COLORS['WHITE'],
                            size=sub2_size,
                            #top=True
                        )
                        
                        merger.merge()
                        self.logger.info(f"Successfully merged subtitles for episode {ep_num}")
                        
                    except Exception as e:
                        self.logger.error(f"Error merging subtitles for episode {ep_num}: {e}")
                        continue
                    
                except Exception as e:
                    self.logger.error(f"Error processing video file {video_file}: {e}")
            
            self.logger.info("Merge operation completed")
            
        except Exception as e:
            self.logger.error(f"Error during merge operation: {e}")

    def confirm_overwrite(self, existing_files: List[Path]) -> bool:
        """Show confirmation dialog for overwriting existing files."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Files Already Exist")
        msg.setText("The following files already exist:\n\n" + 
                   "\n".join(str(f) for f in existing_files[:5]) + 
                   ("\n..." if len(existing_files) > 5 else ""))
        msg.setInformativeText("Do you want to overwrite them?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return msg.exec() == QMessageBox.StandardButton.Yes

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable controls during processing."""
        self.batch_merge_button.setEnabled(enabled)
        self.preview_button.setEnabled(enabled)
        self.episode_range.setEnabled(enabled)

    def on_merge_completed(self):
        """Handle completion of the merge process."""
        self.set_controls_enabled(True)
        self.merge_worker = None
        self.logger.info("Batch processing completed")

    def closeEvent(self, event):
        """Handle application closure."""
        if hasattr(self, 'merge_worker') and self.merge_worker and self.merge_worker.isRunning():
            reply = QMessageBox.question(
                self,
                'Confirm Exit',
                'A merge operation is in progress. Do you want to stop it and exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.merge_worker.stop()
                self.merge_worker.wait()
            else:
                event.ignore()
                return
                
        self.logger.info("Application closing")
        event.accept()

    def check_existing_files(self, episode_subs: dict) -> bool:
        """Check if any output files already exist."""
        existing_files = []
        
        for episode_num, subs in episode_subs.items():
            if 'sub1' in subs and 'sub2' in subs:
                base_name = f"Episode_{episode_num}"
                output_path = Path(self.video_dir_entry.text())
                
                # Check for potential output files
                merged_file = output_path / f"{base_name}_merged.srt"
                sub1_copy = output_path / f"{base_name}.sub1.srt"
                sub2_copy = output_path / f"{base_name}.sub2.srt"
                
                for file in [merged_file, sub1_copy, sub2_copy]:
                    if file.exists():
                        existing_files.append(str(file.name))
        
        if existing_files:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Files Already Exist")
            msg.setText("The following files already exist:\n\n" + 
                       "\n".join(existing_files) + 
                       "\n\nDo you want to overwrite them?")
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            return msg.exec() == QMessageBox.StandardButton.Yes
            
        return True

class SubtitleMergerGUI(QMainWindow):
    """Main application window for the Subtitle Merger GUI."""
    
    def __init__(self):
        super().__init__()
        self.merge_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Subtitle Merger")
        
        # Set to fullscreen by default
        self.showMaximized()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Add tabs using the new classes
        self.single_files_tab = SingleFilesTab()
        self.directory_tab = DirectoryTab()
        
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
    #app.setStyle("Fusion")  # Use Fusion style for better dark theme support
    
    window = SubtitleMergerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()