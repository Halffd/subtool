"""Directory Tab - For merging subtitle files in a directory."""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.utils.subtitle_merger import merge_directory
from .base_tab import BaseTab

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