import os
import shutil
import subprocess
import datetime
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QSlider,
    QWidget, QGridLayout, QFileDialog
)
from PyQt5.QtCore import Qt
from .base_tab import BaseTab
from ..utils.merger import Merger, WHITE

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
        """Merge the selected subtitle files."""
        try:
            sub1_file = self.sub1_entry.text()
            sub2_file = self.sub2_entry.text()
            
            if not all([sub1_file, sub2_file]):
                self.logger.error("Please select both subtitle files")
                return
            
            # Create a new config file with the basename of the directory and date
            self.create_new_config_file(sub1_file)
            
            # Create output path
            output_path = Path(sub1_file).parent
            base_name = Path(sub1_file).stem
            
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
                color=self.color_combo.currentText(),  # Already in hex format
                size=self.sub1_font_slider.value(),
                time_offset=self.sub1_sync_spinbox.value()
            )
            
            # Add second subtitle with size and sync delay
            merger.add(
                sub2_file,
                codec=self.codec_combo.currentText(),
                color=WHITE,  # Use constant from merger.py
                size=self.sub2_font_slider.value(),
                time_offset=self.sub2_sync_spinbox.value()
            )
            
            merger.merge()
            self.logger.info(f"Successfully merged subtitles to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error during merge operation: {e}")

    def create_new_config_file(self, file_path):
        """Create a new configuration file with the basename of the directory and date."""
        try:
            # Get the basename of the directory containing the file
            dir_basename = Path(file_path).parent.name
            
            # Clean the basename to make it suitable for a filename
            # Replace spaces and special characters with underscores
            clean_basename = re.sub(r'[^\w\-]', '_', dir_basename)
            
            # Get current date and time
            now = datetime.datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M%S")
            
            # Create a new config filename
            new_config_filename = f"config_{clean_basename}_{date_str}.json"
            new_config_path = self.config_dir / new_config_filename
            
            # Save current settings to the new file
            self.save_all_values()
            
            # Copy the current settings file to the new file
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as src_file:
                    settings_data = src_file.read()
                    
                with open(new_config_path, 'w', encoding='utf-8') as dest_file:
                    dest_file.write(settings_data)
                
                self.logger.info(f"Created new configuration file: {new_config_filename}")
            else:
                self.logger.warning("No settings file exists to copy")
                
        except Exception as e:
            self.logger.error(f"Error creating new configuration file: {e}")

    def browse_file(self, entry: QLineEdit, title: str):
        """Browse for a subtitle file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, title, "", "Subtitle Files (*.srt);;All Files (*)"
        )
        if file_path:
            entry.setText(file_path)
