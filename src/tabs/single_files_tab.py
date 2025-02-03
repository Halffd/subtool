"""Single Files Tab - For merging individual subtitle files."""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class MergeWorker(QThread):
    """Worker thread for merging subtitle files."""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, input_files, output_file):
        super().__init__()
        self.input_files = input_files
        self.output_file = output_file
        self._stop = False
    
    def run(self):
        """Run the merge operation."""
        try:
            # TODO: Implement actual subtitle merging logic here
            # For now, just simulate progress
            for i in range(101):
                if self._stop:
                    return
                self.progress.emit(i)
                self.msleep(50)  # Simulate work
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Stop the merge operation."""
        self._stop = True

class SingleFilesTab(QWidget):
    """Tab for merging individual subtitle files."""
    
    def __init__(self):
        super().__init__()
        self.input_files = []
        self.merge_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # File list
        self.file_list = QListWidget()
        layout.addWidget(QLabel("Selected Files:"))
        layout.addWidget(self.file_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Files")
        self.add_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Merge section
        merge_layout = QHBoxLayout()
        
        self.merge_btn = QPushButton("Merge Subtitles")
        self.merge_btn.clicked.connect(self.start_merge)
        self.merge_btn.setEnabled(False)
        merge_layout.addWidget(self.merge_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        merge_layout.addWidget(self.progress_bar)
        
        layout.addLayout(merge_layout)
        
        # Connect file list selection signal
        self.file_list.itemSelectionChanged.connect(self.update_button_states)
        
        self.setLayout(layout)
    
    def add_files(self):
        """Open file dialog to add subtitle files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Subtitle Files",
            str(Path.home()),
            "Subtitle Files (*.srt);;All Files (*.*)"
        )
        
        if files:
            self.input_files.extend(files)
            self.file_list.clear()
            self.file_list.addItems([Path(f).name for f in self.input_files])
            self.update_button_states()
    
    def remove_selected(self):
        """Remove selected files from the list."""
        selected_rows = [item.row() for item in self.file_list.selectedItems()]
        for row in sorted(selected_rows, reverse=True):
            self.input_files.pop(row)
            self.file_list.takeItem(row)
        self.update_button_states()
    
    def clear_files(self):
        """Clear all files from the list."""
        self.input_files.clear()
        self.file_list.clear()
        self.update_button_states()
    
    def update_button_states(self):
        """Update button states based on current selection."""
        has_files = bool(self.input_files)
        has_selection = bool(self.file_list.selectedItems())
        
        self.remove_btn.setEnabled(has_selection)
        self.clear_btn.setEnabled(has_files)
        self.merge_btn.setEnabled(has_files and len(self.input_files) > 1)
    
    def start_merge(self):
        """Start the merge operation."""
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged Subtitle",
            str(Path.home()),
            "Subtitle File (*.srt)"
        )
        
        if not output_file:
            return
        
        # Ensure .srt extension
        if not output_file.lower().endswith('.srt'):
            output_file += '.srt'
        
        # Disable UI elements
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.merge_worker = MergeWorker(self.input_files, output_file)
        self.merge_worker.progress.connect(self.update_progress)
        self.merge_worker.finished.connect(self.merge_finished)
        self.merge_worker.error.connect(self.merge_error)
        self.merge_worker.start()
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements."""
        self.add_btn.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled and bool(self.file_list.selectedItems()))
        self.clear_btn.setEnabled(enabled and bool(self.input_files))
        self.merge_btn.setEnabled(enabled and len(self.input_files) > 1)
        self.file_list.setEnabled(enabled)
    
    def update_progress(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
    
    def merge_finished(self):
        """Handle merge completion."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Success", "Subtitles merged successfully!")
        self.merge_worker = None
    
    def merge_error(self, error_msg):
        """Handle merge error."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Failed to merge subtitles: {error_msg}")
        self.merge_worker = None 