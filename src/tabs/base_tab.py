from pathlib import Path
import logging
import sys
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGroupBox,
    QLabel, QPushButton, QLineEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QSlider, QScrollBar,
    QApplication, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QEvent
from ..utils.merger import RED, BLUE, GREEN, WHITE, YELLOW

# Base class for all tabs
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
        
        # Color combo - use constants from merger.py
        self.color_combo = QComboBox()
        self.color_combo.addItems([
            YELLOW,  # Default yellow
            WHITE,
            BLUE,
            RED,
            GREEN
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
        initial_color = self.settings.get('color', YELLOW)  # Use YELLOW constant as default
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
        # Color is already in hex format from merger.py constants
        self.color_preview.setStyleSheet(
            f"background-color: {color_name}; border: 1px solid black;"
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

