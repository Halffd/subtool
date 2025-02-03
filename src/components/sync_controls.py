"""Subtitle synchronization controls and ALASS integration."""

import os
import shutil
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSlider, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt

class SyncControls(QWidget):
    """Widget containing subtitle synchronization controls."""
    
    def __init__(self, parent=None, settings=None, logger=None):
        super().__init__(parent)
        self.settings = settings or {}
        self.logger = logger
        self.alass_path = shutil.which('alass') or '/usr/bin/alass'
        self.setup_ui()

    def setup_ui(self):
        """Setup the sync controls UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)

        # Basic sync controls
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
        layout.addWidget(sync_group)

        # ALASS settings
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
        layout.addWidget(alass_group)

        # Connect sync control signals
        self.sub1_sync_slider.valueChanged.connect(self.sub1_sync_spinbox.setValue)
        self.sub1_sync_spinbox.valueChanged.connect(self.sub1_sync_slider.setValue)
        self.sub2_sync_slider.valueChanged.connect(self.sub2_sync_spinbox.setValue)
        self.sub2_sync_spinbox.valueChanged.connect(self.sub2_sync_slider.setValue)

    def sync_subtitle_with_alass(self, video_path: str, subtitle_path: str) -> str:
        """Synchronize subtitle with ALASS using the video as reference."""
        try:
            if not os.path.exists(self.alass_path):
                if self.logger:
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
            
            if self.logger:
                self.logger.debug(f"Running ALASS command: {' '.join(cmd)}")
            
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                if self.logger:
                    self.logger.error(f"ALASS sync failed: {process.stderr}")
                return subtitle_path
            
            if self.logger:
                self.logger.info(f"ALASS sync successful, output saved to {synced_path}")
            return str(synced_path)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during ALASS sync: {e}")
            return subtitle_path

    def get_sync_values(self):
        """Get current sync values for both subtitles."""
        return {
            'sub1_sync': self.sub1_sync_spinbox.value(),
            'sub2_sync': self.sub2_sync_spinbox.value()
        }

    def get_alass_settings(self):
        """Get current ALASS settings."""
        return {
            'use_alass': self.use_alass.isChecked(),
            'disable_fps_guessing': self.disable_fps_guessing.isChecked(),
            'interval': self.alass_interval.value(),
            'split_penalty': self.alass_split_penalty.value(),
            'sub_fps': self.alass_sub_fps.value(),
            'ref_fps': self.alass_ref_fps.value()
        } 