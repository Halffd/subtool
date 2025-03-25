from pathlib import Path
import logging
import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGroupBox,
    QLabel, QPushButton, QLineEdit, QTextEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QSlider, QScrollBar,
    QApplication, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QEvent
from ..utils.merger import RED, BLUE, GREEN, WHITE, YELLOW

# Base class for all tabs
class BaseTab(QWidget):
    """Base class for tabs with common functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define default style - update to include window borders and title bar
        self.default_style = """
            /* Main window and all widgets */
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-size: 11px;
                border: none;
            }
            
            /* Title bar and window frame */
            QMainWindow::title {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            
            /* Group boxes */
            QGroupBox {
                border: 1px solid #533483;
                margin-top: 0.5em;
                padding-top: 0.5em;
                background-color: #1a1a2e;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            
            /* Input widgets */
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                padding: 2px;
                color: #e0e0e0;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #0f3460;
                border: 1px solid #533483;
                padding: 3px 8px;
                min-height: 20px;
                color: #e0e0e0;
            }
            
            QPushButton:hover {
                background-color: #533483;
            }
            
            /* Sliders */
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
            
            /* Checkboxes */
            QCheckBox {
                spacing: 3px;
                background-color: #1a1a2e;
                color: #e0e0e0;
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
            
            /* Tab widget */
            QTabWidget::pane {
                border: 1px solid #533483;
                background-color: #1a1a2e;
            }
            
            QTabWidget::tab-bar {
                left: 5px;
                background-color: #1a1a2e;
            }
            
            QTabBar::tab {
                background-color: #16213e;
                border: 1px solid #533483;
                padding: 5px 10px;
                margin-right: 2px;
                color: #e0e0e0;
            }
            
            QTabBar::tab:selected {
                background-color: #0f3460;
            }
            
            QTabBar::tab:hover {
                background-color: #533483;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 12px;
                margin: 0;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background: #533483;
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
            
            /* Menu and status bar */
            QMenuBar, QStatusBar {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            
            QMenuBar::item {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            
            QMenuBar::item:selected {
                background-color: #533483;
            }
            
            /* Tooltips */
            QToolTip {
                background-color: #16213e;
                color: #e0e0e0;
                border: 1px solid #533483;
            }
        """
        
        # Create config directory in the application folder
        self.config_dir = Path(__file__).resolve().parent.parent.parent / 'conf'
        self.config_dir.mkdir(exist_ok=True)
        
        # Define settings and log file paths
        self.settings_file = self.config_dir / 'configs.json'
        self.log_file = self.config_dir / 'subtitle_merger.log'
        
        # Setup logging first
        self.setup_logging()
        self.logger = logging.getLogger('SubtitleMerger')
        
        # Load settings before UI setup
        try:
            self.settings = self.load_settings()
            if self.settings is None:
                self.logger.error("Failed to load settings, using defaults")
                self.settings = {
                    'ui_scale': 275,
                    'sub1_font_size': 16,
                    'sub2_font_size': 16,
                    'color': 'Yellow',
                    'codec': 'UTF-8'
                }
        except Exception as e:
            self.logger.error(f"Error during settings initialization: {e}")
            self.settings = {
                'ui_scale': 275,
                'sub1_font_size': 16,
                'sub2_font_size': 16,
                'color': 'Yellow',
                'codec': 'UTF-8'
            }
        
        # Initialize UI elements as class attributes
        self.layout = None
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
        self.option_convert_to_ass = None
        
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
        # Initialize layout as an instance
        layout = QVBoxLayout()
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        
        # Store the layout reference
        self.layout = layout
        
        # Enable focus for key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Now that UI is set up, connect signals
        self.connect_signals()
        
        # Continue with UI setup
        try:
            self.setup_ui()
        except Exception as e:
            self.logger.error(f"Error during UI setup: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        # Set style sheet for the entire application
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.default_style)

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
            
            # If the object is not a scrollbar, block the scroll event
            if not isinstance(obj, QScrollBar):
                return True  # Block scrolling
            
            # Allow scrolling when over scrollbar
            return False  # Let the event propagate
                
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
        
        # Install event filter on the scroll area and its viewport
        for scroll_area in self.findChildren(QScrollArea):
            scroll_area.installEventFilter(self)
            scroll_area.viewport().installEventFilter(self)

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
        self.layout.addWidget(scale_group)
        
        # Connect signals
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        self.scale_input.valueChanged.connect(self.on_scale_changed)
        
        # Set initial value from settings
        initial_scale = self.settings.get('ui_scale', 375)
        self.scale_slider.setValue(initial_scale)
        self.scale_input.setValue(initial_scale)
        self.update_scale(initial_scale)

    def setup_subtitle_sizes(self):
        """Setup subtitle font size controls."""
        font_group = QGroupBox("Subtitle Font Sizes and Thickness")
        font_layout = QVBoxLayout()
        
        # Sub1 font size
        sub1_layout = QHBoxLayout()
        sub1_layout.addWidget(QLabel("Sub1 Font Size:"))
        
        self.sub1_font_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub1_font_slider.setMinimum(8)
        self.sub1_font_slider.setMaximum(48)
        self.sub1_font_slider.setValue(self.settings.get('sub1_font_size', 16))
        
        self.sub1_font_spinbox = QSpinBox()
        self.sub1_font_spinbox.setMinimum(8)
        self.sub1_font_spinbox.setMaximum(48)
        self.sub1_font_spinbox.setValue(self.settings.get('sub1_font_size', 16))
        
        # Connect slider and spinbox (these are local connections, not for saving)
        self.sub1_font_slider.valueChanged.connect(self.sub1_font_spinbox.setValue)
        self.sub1_font_spinbox.valueChanged.connect(self.sub1_font_slider.setValue)
        
        sub1_layout.addWidget(self.sub1_font_slider)
        sub1_layout.addWidget(self.sub1_font_spinbox)
        
        # Sub1 thickness
        sub1_thickness_layout = QHBoxLayout()
        sub1_thickness_layout.addWidget(QLabel("Sub1 Thickness:"))
        
        self.sub1_thickness_checkbox = QCheckBox("Bold")
        self.sub1_thickness_checkbox.setChecked(self.settings.get('sub1_bold', False))
        sub1_thickness_layout.addWidget(self.sub1_thickness_checkbox)
        
        # Sub2 font size
        sub2_layout = QHBoxLayout()
        sub2_layout.addWidget(QLabel("Sub2 Font Size:"))
        
        self.sub2_font_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub2_font_slider.setMinimum(8)
        self.sub2_font_slider.setMaximum(48)
        self.sub2_font_slider.setValue(self.settings.get('sub2_font_size', 16))
        
        self.sub2_font_spinbox = QSpinBox()
        self.sub2_font_spinbox.setMinimum(8)
        self.sub2_font_spinbox.setMaximum(48)
        self.sub2_font_spinbox.setValue(self.settings.get('sub2_font_size', 16))
        
        # Connect slider and spinbox (these are local connections, not for saving)
        self.sub2_font_slider.valueChanged.connect(self.sub2_font_spinbox.setValue)
        self.sub2_font_spinbox.valueChanged.connect(self.sub2_font_slider.setValue)
        
        sub2_layout.addWidget(self.sub2_font_slider)
        sub2_layout.addWidget(self.sub2_font_spinbox)
        
        # Sub2 thickness
        sub2_thickness_layout = QHBoxLayout()
        sub2_thickness_layout.addWidget(QLabel("Sub2 Thickness:"))
        
        self.sub2_thickness_checkbox = QCheckBox("Bold")
        self.sub2_thickness_checkbox.setChecked(self.settings.get('sub2_bold', False))
        sub2_thickness_layout.addWidget(self.sub2_thickness_checkbox)
        
        font_layout.addLayout(sub1_layout)
        font_layout.addLayout(sub1_thickness_layout)
        font_layout.addLayout(sub2_layout)
        font_layout.addLayout(sub2_thickness_layout)
        
        font_group.setLayout(font_layout)
        self.layout.addWidget(font_group)

    def setup_color_selection(self):
        """Setup color selection."""
        color_group = QGroupBox("Subtitle Color")
        color_layout = QVBoxLayout()
        
        # Add description
        description = QLabel("Select the color for the first subtitle:")
        description.setWordWrap(True)
        color_layout.addWidget(description)
        
        # Color selection combo box
        self.color_combo = QComboBox()
        self.color_combo.addItems([
            "Yellow", "White", "Red", "Blue", "Green"
        ])
        
        # Color preview
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(50, 20)
        self.color_preview.setStyleSheet("background-color: Yellow; border: 1px solid black;")
        
        # Custom color button
        custom_color_btn = QPushButton("Custom Color")
        custom_color_btn.clicked.connect(self.on_color_picker_clicked)
        
        # Layout for color selection
        color_select_layout = QHBoxLayout()
        color_select_layout.addWidget(self.color_combo)
        color_select_layout.addWidget(self.color_preview)
        color_select_layout.addWidget(custom_color_btn)
        
        color_layout.addLayout(color_select_layout)
        color_group.setLayout(color_layout)
        self.layout.addWidget(color_group)
        
        # Set initial color from settings
        initial_color = self.settings.get('color', 'Yellow')
        index = self.color_combo.findText(initial_color)
        if index >= 0:
            self.color_combo.setCurrentIndex(index)
            self.update_color_preview(initial_color)
            
        # Connect color change to preview update
        self.color_combo.currentTextChanged.connect(self.update_color_preview)

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

    def setup_options(self):
        """Setup options section."""
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.option_merge_subtitles = QCheckBox("Merge Subtitles Automatically")
        self.option_merge_subtitles.setChecked(
            self.settings.get('merge_automatically', True)
        )
        
        self.option_generate_log = QCheckBox("Generate Log File")
        self.option_generate_log.setChecked(
            self.settings.get('generate_log', False)
        )
        
        # Add option for ASS conversion with furigana
        self.option_convert_to_ass = QCheckBox("Convert to ASS with Furigana")
        self.option_convert_to_ass.setChecked(
            self.settings.get('convert_to_ass', False)
        )
        self.option_convert_to_ass.setToolTip(
            "Convert SRT files with furigana in parentheses to ASS format with proper ruby text"
        )
        
        # Add SVG filtering options
        svg_options_group = QGroupBox("SVG Options")
        svg_options_layout = QVBoxLayout()
        
        self.option_enable_svg_filtering = QCheckBox("Enable SVG Filtering")
        self.option_enable_svg_filtering.setChecked(
            self.settings.get('enable_svg_filtering', False)
        )
        self.option_enable_svg_filtering.setToolTip(
            "Filter duplicate SVG path entries at the same timestamp"
        )
        
        self.option_remove_text_entries = QCheckBox("Remove Text Entries")
        self.option_remove_text_entries.setChecked(
            self.settings.get('remove_text_entries', False)
        )
        self.option_remove_text_entries.setToolTip(
            "Remove text entries, keeping only SVG path entries"
        )
        
        self.option_preserve_svg = QCheckBox("Preserve SVG Paths")
        self.option_preserve_svg.setChecked(
            self.settings.get('preserve_svg', True)
        )
        self.option_preserve_svg.setToolTip(
            "Preserve SVG path data when merging subtitles"
        )
        
        svg_options_layout.addWidget(self.option_enable_svg_filtering)
        svg_options_layout.addWidget(self.option_remove_text_entries)
        svg_options_layout.addWidget(self.option_preserve_svg)
        svg_options_group.setLayout(svg_options_layout)
        
        options_layout.addWidget(self.option_merge_subtitles)
        options_layout.addWidget(self.option_generate_log)
        options_layout.addWidget(self.option_convert_to_ass)
        options_layout.addWidget(svg_options_group)
        
        # Add button to load previous configurations
        load_config_btn = QPushButton("Load Previous Configuration")
        load_config_btn.clicked.connect(self.load_previous_config)
        options_layout.addWidget(load_config_btn)
        
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
            'codec': self.codec_combo.currentText(),
            'enable_svg_filtering': self.option_enable_svg_filtering.isChecked(),
            'remove_text_entries': self.option_remove_text_entries.isChecked(),
            'preserve_svg': self.option_preserve_svg.isChecked()
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
            'sub1_pattern': r'Squid Girl - S01E\d+\.large-v3.*\.srt$',  # Match large-v3 subtitles
            'sub2_pattern': r'Squid Girl - S01E\d+\.4\.eng\.srt$',  # Match .4.eng subtitles
            'sub1_episode_pattern': r'S01E(\d+)',  # Extract episode number after S01E
            'sub2_episode_pattern': r'S01E(\d+)',  # Extract episode number after S01E
            'episode_pattern': r'\d+',  # Legacy support
            'auto_detect_mode': False  # Default to manual mode
        }
        
        try:
            # Ensure settings_file exists and is properly initialized
            if not hasattr(self, 'settings_file'):
                self.config_dir = Path(__file__).parent.parent.parent / 'conf'
                self.config_dir.mkdir(exist_ok=True)
                self.settings_file = self.config_dir / 'configs.json'
                
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if hasattr(self, 'logger'):
                        self.logger.debug("Settings loaded successfully")
                    # Merge with defaults in case new settings were added
                    return {**default_settings, **settings}
            else:
                if hasattr(self, 'logger'):
                    self.logger.info("No settings file found, creating with defaults")
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4)
                return default_settings
                
        except Exception as e:
            if hasattr(self, 'logger'):
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
                # Only save values for attributes that exist and are initialized
                if hasattr(self, 'scale_slider') and self.scale_slider is not None and self.scale_slider.value() is not None:
                    self.settings['ui_scale'] = self.scale_slider.value()
                if hasattr(self, 'sub1_font_slider') and self.sub1_font_slider is not None and self.sub1_font_slider.value() is not None:
                    self.settings['sub1_font_size'] = self.sub1_font_slider.value()
                if hasattr(self, 'sub2_font_slider') and self.sub2_font_slider is not None and self.sub2_font_slider.value() is not None:
                    self.settings['sub2_font_size'] = self.sub2_font_slider.value()
                if hasattr(self, 'sub1_thickness_checkbox') and self.sub1_thickness_checkbox is not None:
                    self.settings['sub1_bold'] = self.sub1_thickness_checkbox.isChecked()
                if hasattr(self, 'sub2_thickness_checkbox') and self.sub2_thickness_checkbox is not None:
                    self.settings['sub2_bold'] = self.sub2_thickness_checkbox.isChecked()
                if hasattr(self, 'color_combo') and self.color_combo is not None and self.color_combo.currentText() is not None:
                    self.settings['color'] = self.color_combo.currentText()
                if hasattr(self, 'codec_combo') and self.codec_combo is not None and self.codec_combo.currentText() is not None:
                    self.settings['codec'] = self.codec_combo.currentText()
                if hasattr(self, 'option_merge_subtitles') and self.option_merge_subtitles is not None:
                    self.settings['merge_automatically'] = self.option_merge_subtitles.isChecked()
                if hasattr(self, 'option_generate_log') and self.option_generate_log is not None:
                    self.settings['generate_log'] = self.option_generate_log.isChecked()
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.debug("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def save_value_to_settings(self, key=None, value=None):
        """Save a specific value to settings."""
        try:
            # Handle case when called from a signal that doesn't provide key and value
            if key is None or value is None:
                # Just save all values instead
                self.save_all_values()
                return
                
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
            settings_update = {}
            
            # Only add settings for UI elements that exist and are initialized
            if hasattr(self, 'scale_slider') and self.scale_slider is not None:
                settings_update['ui_scale'] = self.scale_slider.value()
            else:
                settings_update['ui_scale'] = self.settings.get('ui_scale', 375)
                
            if hasattr(self, 'sub1_font_slider') and self.sub1_font_slider is not None:
                settings_update['sub1_font_size'] = self.sub1_font_slider.value()
            else:
                settings_update['sub1_font_size'] = self.settings.get('sub1_font_size', 16)
                
            if hasattr(self, 'sub2_font_slider') and self.sub2_font_slider is not None:
                settings_update['sub2_font_size'] = self.sub2_font_slider.value()
            else:
                settings_update['sub2_font_size'] = self.settings.get('sub2_font_size', 16)
                
            if hasattr(self, 'color_combo') and self.color_combo is not None:
                settings_update['color'] = self.color_combo.currentText()
            else:
                settings_update['color'] = self.settings.get('color', 'Yellow')
                
            if hasattr(self, 'codec_combo') and self.codec_combo is not None:
                settings_update['codec'] = self.codec_combo.currentText()
            else:
                settings_update['codec'] = self.settings.get('codec', 'UTF-8')
                
            if hasattr(self, 'option_merge_subtitles') and self.option_merge_subtitles is not None:
                settings_update['merge_automatically'] = self.option_merge_subtitles.isChecked()
            else:
                settings_update['merge_automatically'] = self.settings.get('merge_automatically', True)
                
            if hasattr(self, 'option_generate_log') and self.option_generate_log is not None:
                settings_update['generate_log'] = self.option_generate_log.isChecked()
            else:
                settings_update['generate_log'] = self.settings.get('generate_log', False)
                
            if hasattr(self, 'option_convert_to_ass') and self.option_convert_to_ass is not None:
                settings_update['convert_to_ass'] = self.option_convert_to_ass.isChecked()
            else:
                settings_update['convert_to_ass'] = self.settings.get('convert_to_ass', False)
            
            # Save SVG filtering options
            if hasattr(self, 'option_enable_svg_filtering') and self.option_enable_svg_filtering is not None:
                settings_update['enable_svg_filtering'] = self.option_enable_svg_filtering.isChecked()
            else:
                settings_update['enable_svg_filtering'] = self.settings.get('enable_svg_filtering', False)
                
            if hasattr(self, 'option_remove_text_entries') and self.option_remove_text_entries is not None:
                settings_update['remove_text_entries'] = self.option_remove_text_entries.isChecked()
            else:
                settings_update['remove_text_entries'] = self.settings.get('remove_text_entries', False)
                
            if hasattr(self, 'option_preserve_svg') and self.option_preserve_svg is not None:
                settings_update['preserve_svg'] = self.option_preserve_svg.isChecked()
            else:
                settings_update['preserve_svg'] = self.settings.get('preserve_svg', True)
            
            # Add directory-specific settings if they exist
            if hasattr(self, 'dir_entry') and self.dir_entry is not None and self.dir_entry.text():
                settings_update['last_subtitle_directory'] = self.dir_entry.text()
                settings_update['last_directory'] = str(Path(self.dir_entry.text()).parent)
            
            if hasattr(self, 'video_dir_entry') and self.video_dir_entry is not None and self.video_dir_entry.text():
                settings_update['last_video_directory'] = self.video_dir_entry.text()
            
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
        else:
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

    def load_previous_config(self):
        """Show a dialog to select and load a previous configuration."""
        try:
            # Get list of config files
            config_files = list(self.config_dir.glob("config_*.json"))
            
            if not config_files:
                QMessageBox.information(self, "No Configurations", 
                                       "No previous configurations found.")
                return
            
            # Sort by modification time (newest first)
            config_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Create a simple dialog to select a config file
            selected_item = QFileDialog.getOpenFileName(
                self, 
                "Select Configuration File",
                str(self.config_dir),
                "JSON Files (*.json)"
            )[0]  # Get the first element of the tuple
            
            if not selected_item:
                return
                
            selected_path = Path(selected_item)
            
            # Load the selected config
            with open(selected_path, 'r', encoding='utf-8') as f:
                new_settings = json.load(f)
                
            # Update current settings
            self.settings.update(new_settings)
            
            # Save to current settings file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
                
            # Reload UI with new settings
            self.reload_settings()
            
            self.logger.info(f"Loaded configuration from {selected_path.name}")
            QMessageBox.information(self, "Configuration Loaded", 
                                   f"Successfully loaded configuration from {selected_path.name}")
                
        except Exception as e:
            self.logger.error(f"Error loading previous configuration: {e}")
            QMessageBox.critical(self, "Error", f"Error loading configuration: {e}")
    
    def reload_settings(self):
        """Reload UI elements with current settings."""
        # Update UI scale
        if hasattr(self, 'scale_slider'):
            self.scale_slider.setValue(self.settings.get('ui_scale', 375))
            
        # Update font sizes
        if hasattr(self, 'sub1_font_slider'):
            self.sub1_font_slider.setValue(self.settings.get('sub1_font_size', 16))
        if hasattr(self, 'sub2_font_slider'):
            self.sub2_font_slider.setValue(self.settings.get('sub2_font_size', 16))
            
        # Update thickness settings
        if hasattr(self, 'sub1_thickness_checkbox'):
            self.sub1_thickness_checkbox.setChecked(self.settings.get('sub1_bold', False))
        if hasattr(self, 'sub2_thickness_checkbox'):
            self.sub2_thickness_checkbox.setChecked(self.settings.get('sub2_bold', False))
            
        # Update color
        if hasattr(self, 'color_combo'):
            color = self.settings.get('color', 'Yellow')
            index = self.color_combo.findText(color)
            if index >= 0:
                self.color_combo.setCurrentIndex(index)
                
        # Update codec
        if hasattr(self, 'codec_combo'):
            codec = self.settings.get('codec', 'UTF-8')
            index = self.codec_combo.findText(codec)
            if index >= 0:
                self.codec_combo.setCurrentIndex(index)
                
        # Update options
        if hasattr(self, 'option_merge_subtitles'):
            self.option_merge_subtitles.setChecked(
                self.settings.get('merge_automatically', True)
            )
        if hasattr(self, 'option_generate_log'):
            self.option_generate_log.setChecked(
                self.settings.get('generate_log', False)
            )
        if hasattr(self, 'option_convert_to_ass'):
            self.option_convert_to_ass.setChecked(
                self.settings.get('convert_to_ass', False)
            )
            
        # Update pattern entries if they exist
        if hasattr(self, 'sub1_pattern_entry'):
            self.sub1_pattern_entry.setText(
                self.settings.get('sub1_pattern', '')
            )
        if hasattr(self, 'sub2_pattern_entry'):
            self.sub2_pattern_entry.setText(
                self.settings.get('sub2_pattern', '')
            )
        if hasattr(self, 'sub1_episode_pattern_entry'):
            self.sub1_episode_pattern_entry.setText(
                self.settings.get('sub1_episode_pattern', '')
            )
        if hasattr(self, 'sub2_episode_pattern_entry'):
            self.sub2_episode_pattern_entry.setText(
                self.settings.get('sub2_episode_pattern', '')
            )
            
        self.logger.debug("Settings reloaded in UI")

    def connect_signals(self):
        """Connect signals for all UI elements."""
        # Connect signals for specific UI elements
        if hasattr(self, 'sub1_font_slider') and self.sub1_font_slider is not None:
            self.sub1_font_slider.valueChanged.connect(lambda v: self.save_value_to_settings('sub1_font_size', v))
            
        if hasattr(self, 'sub2_font_slider') and self.sub2_font_slider is not None:
            self.sub2_font_slider.valueChanged.connect(lambda v: self.save_value_to_settings('sub2_font_size', v))
            
        if hasattr(self, 'sub1_thickness_checkbox') and self.sub1_thickness_checkbox is not None:
            self.sub1_thickness_checkbox.stateChanged.connect(lambda: self.save_value_to_settings('sub1_bold', self.sub1_thickness_checkbox.isChecked()))
            
        if hasattr(self, 'sub2_thickness_checkbox') and self.sub2_thickness_checkbox is not None:
            self.sub2_thickness_checkbox.stateChanged.connect(lambda: self.save_value_to_settings('sub2_bold', self.sub2_thickness_checkbox.isChecked()))
            
        if hasattr(self, 'color_combo') and self.color_combo is not None:
            self.color_combo.currentTextChanged.connect(lambda: self.save_all_values())
            
        if hasattr(self, 'codec_combo') and self.codec_combo is not None:
            self.codec_combo.currentTextChanged.connect(lambda: self.save_all_values())
            
        if hasattr(self, 'option_merge_subtitles') and self.option_merge_subtitles is not None:
            self.option_merge_subtitles.stateChanged.connect(lambda: self.save_all_values())
            
        if hasattr(self, 'option_generate_log') and self.option_generate_log is not None:
            self.option_generate_log.stateChanged.connect(lambda: self.save_all_values())
            
        if hasattr(self, 'option_convert_to_ass') and self.option_convert_to_ass is not None:
            self.option_convert_to_ass.stateChanged.connect(lambda: self.save_all_values())

