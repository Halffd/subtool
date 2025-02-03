"""Directory Tab - For merging subtitle files in a directory."""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QMessageBox, QLineEdit,
    QSlider, QSpinBox, QGroupBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.utils.subtitle_merger import merge_directory
from src.utils.settings import Settings, DEFAULT_SETTINGS
from src.tabs.base_tab import BaseTab

class DirectoryMergeWorker(QThread):
    """Worker thread for merging subtitle files in a directory."""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    
    def __init__(self, input_dir, output_dir, pattern):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.pattern = pattern
        self._stop = False
    
    def run(self):
        """Run the merge operation."""
        try:
            if self._stop:
                return
            
            # Start directory merge
            self.progress.emit(10)
            self.log.emit(f"Starting directory merge with pattern: {self.pattern}")
            merge_directory(self.input_dir, self.output_dir, self.pattern)
            
            if not self._stop:
                self.progress.emit(100)
                self.log.emit("Directory merge completed successfully")
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Stop the merge operation."""
        self._stop = True

class DirectoryTab(BaseTab):
    """Tab for merging subtitle files in a directory."""
    
    def __init__(self, parent=None):
        super().__init__("directory", parent)
        self.input_dir = None
        self.output_dir = None
        self.merge_worker = None
        self.settings = Settings(Path.home() / '.config' / 'srtmerger')
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Input directory section
        input_layout = QHBoxLayout()
        self.input_dir_label = QLabel("No input directory selected")
        input_layout.addWidget(self.input_dir_label)
        
        self.select_input_btn = QPushButton("Select Input Directory")
        self.select_input_btn.clicked.connect(self.select_input_directory)
        input_layout.addWidget(self.select_input_btn)
        
        self.layout.addLayout(input_layout)
        
        # Pattern section
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("File Pattern:"))
        
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("e.g., *_en.srt, *_fr.srt")
        pattern_layout.addWidget(self.pattern_edit)
        
        self.layout.addLayout(pattern_layout)
        
        # Output directory section
        output_layout = QHBoxLayout()
        self.output_dir_label = QLabel("No output directory selected")
        output_layout.addWidget(self.output_dir_label)
        
        self.select_output_btn = QPushButton("Select Output Directory")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        output_layout.addWidget(self.select_output_btn)
        
        self.layout.addLayout(output_layout)
        
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
        
        # Merge section
        merge_layout = QHBoxLayout()
        
        self.merge_btn = QPushButton("Merge Subtitles")
        self.merge_btn.clicked.connect(self.start_merge)
        self.merge_btn.setEnabled(False)
        merge_layout.addWidget(self.merge_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        merge_layout.addWidget(self.progress_bar)
        
        self.layout.addLayout(merge_layout)
        
        # Add stretch to push log section to bottom
        self.layout.addStretch()
        
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

    def save_value_to_settings(self, key: str, value: str):
        """Save a value to settings."""
        self.settings.set(key, value)

    def on_scale_changed(self, value: int):
        """Handle scale value change."""
        self.scale_slider.setValue(value)
        self.scale_input.setValue(value)
        self.update_scale(value)
        self.save_value_to_settings('ui_scale', value)

    def update_scale(self, value: int):
        """Update UI scale."""
        # Implementation depends on how you want to handle scaling
        pass

    def adjust_scale(self, delta: int):
        """Adjust scale by delta."""
        current = self.scale_slider.value()
        self.scale_slider.setValue(current + delta)

    def update_color_preview(self, color_name: str):
        """Update color preview label."""
        # Implementation depends on your color handling
        pass

    def on_color_picker_clicked(self):
        """Handle color picker button click."""
        # Implementation depends on your color picker handling
        pass

    def select_input_directory(self):
        """Open directory dialog to select input directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Input Directory",
            str(Path.home())
        )
        
        if directory:
            self.input_dir = directory
            self.input_dir_label.setText(f"Input: {Path(directory).name}")
            self.update_merge_button()
            self.logger.info(f"Selected input directory: {directory}")
    
    def select_output_directory(self):
        """Open directory dialog to select output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if directory:
            self.output_dir = directory
            self.output_dir_label.setText(f"Output: {Path(directory).name}")
            self.update_merge_button()
            self.logger.info(f"Selected output directory: {directory}")
    
    def update_merge_button(self):
        """Update merge button state based on current selection."""
        pattern = self.pattern_edit.text().strip()
        self.merge_btn.setEnabled(
            bool(self.input_dir) and
            bool(self.output_dir) and
            bool(pattern)
        )
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements."""
        self.select_input_btn.setEnabled(enabled)
        self.select_output_btn.setEnabled(enabled)
        self.pattern_edit.setEnabled(enabled)
        self.merge_btn.setEnabled(enabled and bool(self.input_dir) and bool(self.output_dir))
    
    def start_merge(self):
        """Start the merge operation."""
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Warning", "Please enter a file pattern")
            return
        
        # Disable UI elements
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.merge_worker = DirectoryMergeWorker(self.input_dir, self.output_dir, pattern)
        self.merge_worker.progress.connect(self.update_progress)
        self.merge_worker.finished.connect(self.merge_finished)
        self.merge_worker.error.connect(self.merge_error)
        self.merge_worker.log.connect(self.logger.info)
        self.merge_worker.start()
        
        self.logger.info("Starting directory merge operation...")
    
    def update_progress(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
    
    def merge_finished(self):
        """Handle merge completion."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.logger.info("Directory merge completed successfully!")
        QMessageBox.information(self, "Success", "Directory subtitles merged successfully!")
        self.merge_worker = None
    
    def merge_error(self, error_msg):
        """Handle merge error."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.logger.error(f"Directory merge failed: {error_msg}")
        QMessageBox.critical(self, "Error", f"Failed to merge subtitles: {error_msg}")
        self.merge_worker = None 