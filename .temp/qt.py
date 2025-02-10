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