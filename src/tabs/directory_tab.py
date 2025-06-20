#!/usr/bin/env python
# Directory Tab - A tab for batch processing subtitle files in a directory

import os
import re
import datetime
import sys
import glob
import traceback
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox,
    QFileDialog, QLineEdit, QGroupBox, QHBoxLayout, QApplication,
    QSpinBox, QCheckBox, QProgressBar
)
import json
import logging

from .base_tab import BaseTab
from ..utils.merger import Merger, WHITE, YELLOW
from ..utils.ass_converter import create_ass_from_srt, process_directory as process_ass_directory
from ..utils.pattern_guesser import suggest_patterns

class DirectoryTab(BaseTab):
    """Tab for processing directories."""
    
    def __init__(self, parent=None):
        # Call parent init first
        super().__init__(parent)
        
        # Initialize auto-detection mode (will be updated from settings later)
        self.auto_detect_mode = False
        
        # Set up logger for this tab
        self.logger = logging.getLogger("SubtitleMerger.DirectoryTab")
        
        # Load settings first
        self.settings = self.load_settings()
        
        # Setup UI components specific to directory tab
        self.dir_entry = None
        self.video_dir_entry = None
        self.sub1_pattern_entry = None
        self.sub2_pattern_entry = None
        self.sub1_episode_pattern_entry = None
        self.sub2_episode_pattern_entry = None
        self.batch_merge_button = None
        
        # Subtitle delay components
        self.sub1_delay_spinner = None
        self.sub2_delay_spinner = None
        
        # ALASS auto-sync components
        self.enable_alass_sync = None
        self.alass_path_entry = None
        
        # Setup UI
        self.setup_directory_ui()
        
        # Update UI elements based on loaded settings
        self.update_ui_from_settings()
        
        # Connect any signals specific to this tab
        self.connect_signals()
        
        self.logger.debug("DirectoryTab initialized with settings")

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

        # Add auto-detection mode toggle
        self.auto_mode_toggle = QPushButton()
        self.auto_mode_toggle.setCheckable(True)
        self.auto_mode_toggle.setChecked(self.auto_detect_mode)
        self.auto_mode_toggle.clicked.connect(self.toggle_detection_mode)
        self.update_toggle_button_text()
        pattern_layout.addWidget(self.auto_mode_toggle)

        # Filter patterns section
        self.pattern_widgets_container = QWidget()
        self.manual_pattern_layout = QVBoxLayout(self.pattern_widgets_container)
        
        self.manual_pattern_layout.addWidget(QLabel("Filter Patterns:"))

        # Create pattern entries
        sub1_filter_layout, self.sub1_pattern_entry = self._create_pattern_entry(
            "Sub1 (Main):",
            'sub1_pattern',
            "Pattern to identify main subtitle files"
        )
        self.manual_pattern_layout.addLayout(sub1_filter_layout)

        sub2_filter_layout, self.sub2_pattern_entry = self._create_pattern_entry(
            "Sub2 (Secondary):",
            'sub2_pattern',
            "Pattern to identify secondary subtitle files"
        )
        self.manual_pattern_layout.addLayout(sub2_filter_layout)

        # Episode patterns section
        self.manual_pattern_layout.addWidget(QLabel("Episode Number Patterns:"))

        sub1_ep_layout, self.sub1_episode_pattern_entry = self._create_pattern_entry(
            "Sub1 (Japanese):",
            'sub1_episode_pattern',
            "Pattern to find episode numbers in Japanese subtitle files"
        )
        self.manual_pattern_layout.addLayout(sub1_ep_layout)

        sub2_ep_layout, self.sub2_episode_pattern_entry = self._create_pattern_entry(
            "Sub2 (Non-Japanese):",
            'sub2_episode_pattern',
            "Pattern to find episode numbers in non-Japanese subtitle files"
        )
        self.manual_pattern_layout.addLayout(sub2_ep_layout)

        pattern_layout.addWidget(self.pattern_widgets_container)

        # Test patterns button
        test_btn = QPushButton("Test Patterns")
        test_btn.clicked.connect(self.test_patterns)
        
        # Add Guess Patterns button
        self.guess_patterns_btn = QPushButton("Guess Patterns")
        self.guess_patterns_btn.setToolTip("Automatically suggest patterns based on files in the selected directory")
        self.guess_patterns_btn.clicked.connect(self.guess_patterns)
        
        # Add buttons in a horizontal layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(test_btn)
        buttons_layout.addWidget(self.guess_patterns_btn)
        pattern_layout.addLayout(buttons_layout)

        pattern_group.setLayout(pattern_layout)
        self.layout.addWidget(pattern_group)

        # Add subtitle delay group
        delay_group = QGroupBox("Subtitle Timing")
        delay_layout = QVBoxLayout()
        
        # Sub1 (Japanese) delay
        sub1_delay_layout = QHBoxLayout()
        sub1_delay_layout.addWidget(QLabel("Sub1 (Japanese) Delay (ms):"))
        self.sub1_delay_spinner = QSpinBox()
        self.sub1_delay_spinner.setRange(-10000, 10000)
        self.sub1_delay_spinner.setSingleStep(100)
        self.sub1_delay_spinner.setValue(self.settings.get('sub1_delay', 0))
        self.sub1_delay_spinner.setToolTip("Positive values delay subtitles, negative values make them appear earlier")
        self.sub1_delay_spinner.valueChanged.connect(lambda: self.save_value_to_settings('sub1_delay', self.sub1_delay_spinner.value()))
        sub1_delay_layout.addWidget(self.sub1_delay_spinner)
        delay_layout.addLayout(sub1_delay_layout)
        
        # Sub2 (Non-Japanese) delay
        sub2_delay_layout = QHBoxLayout()
        sub2_delay_layout.addWidget(QLabel("Sub2 (Non-Japanese) Delay (ms):"))
        self.sub2_delay_spinner = QSpinBox()
        self.sub2_delay_spinner.setRange(-10000, 10000)
        self.sub2_delay_spinner.setSingleStep(100)
        self.sub2_delay_spinner.setValue(self.settings.get('sub2_delay', 0))
        self.sub2_delay_spinner.setToolTip("Positive values delay subtitles, negative values make them appear earlier")
        self.sub2_delay_spinner.valueChanged.connect(lambda: self.save_value_to_settings('sub2_delay', self.sub2_delay_spinner.value()))
        sub2_delay_layout.addWidget(self.sub2_delay_spinner)
        delay_layout.addLayout(sub2_delay_layout)
        
        # ALASS auto-sync
        alass_group = QGroupBox("Auto-Sync (ALASS)")
        alass_layout = QVBoxLayout()
        
        # Enable ALASS checkbox
        self.enable_alass_sync = QCheckBox("Enable automatic subtitle synchronization using ALASS")
        self.enable_alass_sync.setChecked(self.settings.get('enable_alass_sync', False))
        self.enable_alass_sync.setToolTip("Uses ALASS to automatically synchronize subtitles with video files")
        self.enable_alass_sync.stateChanged.connect(self.toggle_alass_settings)
        alass_layout.addWidget(self.enable_alass_sync)
        
        # ALASS executable path
        alass_path_layout = QHBoxLayout()
        alass_path_layout.addWidget(QLabel("ALASS Path:"))
        self.alass_path_entry = QLineEdit()
        self.alass_path_entry.setText(self.settings.get('alass_path', ''))
        self.alass_path_entry.setToolTip("Path to the ALASS executable. Leave empty to use built-in or system-wide installation.")
        self.alass_path_entry.textChanged.connect(lambda: self.save_value_to_settings('alass_path', self.alass_path_entry.text()))
        alass_path_layout.addWidget(self.alass_path_entry)
        
        alass_browse_btn = QPushButton("Browse")
        alass_browse_btn.clicked.connect(self.browse_alass_path)
        alass_path_layout.addWidget(alass_browse_btn)
        alass_layout.addLayout(alass_path_layout)
        
        alass_group.setLayout(alass_layout)
        delay_layout.addWidget(alass_group)
        
        delay_group.setLayout(delay_layout)
        self.layout.addWidget(delay_group)

        # Add merge button
        self.batch_merge_button = QPushButton("Merge Subtitles")
        self.batch_merge_button.clicked.connect(self.merge_subtitles)
        self.batch_merge_button.setMinimumHeight(40)
        self.layout.addWidget(self.batch_merge_button)

        # Add stretch
        self.layout.addStretch()

        # Add log section last
        self.setup_log_section()
        
        # Update UI based on current mode
        self.set_detection_mode(self.auto_detect_mode)
        
        # Update ALASS settings visibility
        self.toggle_alass_settings()

    def save_directory_settings(self):
        """Save directory settings when they change."""
        try:
            if hasattr(self, 'dir_entry') and hasattr(self, 'video_dir_entry'):
                settings_update = {}
                
                if self.dir_entry and self.dir_entry.text():
                    settings_update['last_subtitle_directory'] = self.dir_entry.text()
                    
                if self.video_dir_entry and self.video_dir_entry.text():
                    settings_update['last_video_directory'] = self.video_dir_entry.text()
                
                if settings_update:
                    self.save_settings(settings_update)
        except Exception as e:
            self.logger.error(f"Error saving directory settings: {e}")

    def save_pattern_settings(self):
        """Save all pattern settings when they change."""
        try:
            if hasattr(self, 'sub1_pattern_entry') and hasattr(self, 'sub2_pattern_entry') and \
               hasattr(self, 'sub1_episode_pattern_entry') and hasattr(self, 'sub2_episode_pattern_entry'):
                settings_update = {}
                
                if self.sub1_pattern_entry and self.sub1_pattern_entry.text() is not None:
                    settings_update['sub1_pattern'] = self.sub1_pattern_entry.text()
                    
                if self.sub2_pattern_entry and self.sub2_pattern_entry.text() is not None:
                    settings_update['sub2_pattern'] = self.sub2_pattern_entry.text()
                    
                if self.sub1_episode_pattern_entry and self.sub1_episode_pattern_entry.text() is not None:
                    settings_update['sub1_episode_pattern'] = self.sub1_episode_pattern_entry.text()
                    
                if self.sub2_episode_pattern_entry and self.sub2_episode_pattern_entry.text() is not None:
                    settings_update['sub2_episode_pattern'] = self.sub2_episode_pattern_entry.text()
                
                if settings_update:
                    self.settings.update(settings_update)
                    self.save_settings()
                    self.logger.debug(f"Pattern settings saved: {settings_update}")
                    
                    # Update UI to reflect saved settings
                    self.update_ui_from_settings()
        except Exception as e:
            self.logger.error(f"Error saving pattern settings: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

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
                # First try SxxExx pattern
                sxxexx_match = re.search(r'[Ss](\d+)[Ee](\d+)', f.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                    sub1_episodes.append((f.name, ep_num))
                else:
                    # Try configured pattern
                    match = re.search(sub1_ep_pattern, f.stem)
                    if match:
                        sub1_episodes.append((f.name, match.group(1)))
                    
            for f in sub2_files[:5]:  # Test first 5 files
                # First try SxxExx pattern
                sxxexx_match = re.search(r'[Ss](\d+)[Ee](\d+)', f.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                    sub2_episodes.append((f.name, ep_num))
                else:
                    # Try configured pattern
                    match = re.search(sub2_ep_pattern, f.stem)
                    if match:
                        sub2_episodes.append((f.name, match.group(1)))
            
            # Show results
            msg = QMessageBox()
            msg.setWindowTitle("Pattern Test Results")
            self.logger.debug('Sub 1: %s', sub1_files)
            self.logger.debug('Sub 2: %s', sub2_files)
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
    def find_episodes(self, sub_files, sub_ep_pattern, sub_name = 'sub', episode_subs = {}):
        for sub1 in sub_files:
            try:
                # First try SxxExx pattern
                sxxexx_match = re.search(r'[Ss](\d+)[Ee](\d+)', sub1.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                else:
                    # Try configured pattern
                    match = re.search(sub_ep_pattern, sub1.stem)
                    if match:
                        ep_num = match.group(1)
                        season_num = '01'  # Default season
                    else:
                        # Try extracting episode number from filename
                        ep_match = re.search(r'(?:^|\s|_|-|\[)(\d{1,2})(?:\s|$|\]|\[|\()', sub1.stem)
                        if ep_match:
                            ep_num = ep_match.group(1)
                            season_num = '01'  # Default season
                        else:
                            self.logger.warning(f"Could not extract episode info from sub1 file: {sub1.name}")
                            continue
                
                # Create a unique key combining season and episode
                ep_key = f"S{season_num}E{ep_num}"
                
                if ep_key not in episode_subs:
                    episode_subs[ep_key] = {
                        sub_name: sub1, 
                        'season': season_num, 
                        'episode': ep_num,
                        'file_name': sub1.name
                    }
                    self.logger.debug(f"Found sub1 for {ep_key}: {sub1.name}")
                elif sub_name != 'sub1' or sub_name != 'sub':
                    episode_subs[ep_key][sub_name] = sub1
                    
            except Exception as e:
                self.logger.error(f"Error processing sub1 file {sub1}: {e}")
        
        return episode_subs
    def merge_subtitles(self):
        """Merge subtitle files in the directory based on patterns."""
        try:
            input_dir = self.dir_entry.text().strip()
            video_dir = self.video_dir_entry.text().strip()
            
            if not all([input_dir, video_dir]):
                self.logger.error("Please select both input and video directories")
                return

            # Create a new config file with the basename of the directory and date
            self.create_new_config_file(input_dir)

            self.logger.info("Starting merge operation...")
            self.logger.info(f"Input directory: {input_dir}")
            self.logger.info(f"Video directory: {video_dir}")
            
            # Find subtitle files (case insensitive)
            try:
                input_path = Path(input_dir)
                video_path = Path(video_dir)
                
                # List all srt files for logging
                all_srt_files = list(input_path.glob('*.srt'))
                self.logger.debug(f"Found {len(all_srt_files)} total .srt files")
                for srt_file in all_srt_files:
                    self.logger.debug(f"Found SRT file: {srt_file.name}")
                
                # Get current patterns from UI
                sub1_pattern = self.sub1_pattern_entry.text()
                sub2_pattern = self.sub2_pattern_entry.text()
                sub1_ep_pattern = self.sub1_episode_pattern_entry.text()
                sub2_ep_pattern = self.sub2_episode_pattern_entry.text()
                
                # Find matching files using the same logic as test_patterns
                sub1_files = [f for f in input_path.glob('*.srt') 
                            if re.search(sub1_pattern, f.name, re.IGNORECASE)]
                sub2_files = [f for f in input_path.glob('*.srt')
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
            
            # Process sub1 files using the same episode extraction as test_patterns
            self.find_episodes(sub1_files, sub1_ep_pattern, 'sub1', episode_subs)
            # Process sub2 files using the same episode extraction as test_patterns
            self.find_episodes(sub2_files, sub2_ep_pattern, 'sub2', episode_subs)
            # Display summary of matched subtitles
            matched_pairs = [k for k, v in episode_subs.items() if 'sub1' in v and 'sub2' in v]

            # If we don't have any matches but have both sub1 and sub2 files, try looser matching
            if not matched_pairs and sub1_files and sub2_files:
                self.logger.warning("No matches found with strict season+episode matching, trying looser matching based on just episode numbers")
                
                # Create a map of just episode numbers to entries
                ep_only_map = {}
                
                # Gather all episodes from sub1 files
                for ep_key, entry in episode_subs.items():
                    if 'sub1' in entry:
                        # Extract just the episode number from the key (format is SxxEyy)
                        ep_num = entry['episode']
                        if ep_num not in ep_only_map:
                            ep_only_map[ep_num] = []
                        ep_only_map[ep_num].append(ep_key)
                
                # Now look for sub2 files that can be matched by episode number
                matched_count = 0
                for ep_key, entry in episode_subs.items():
                    if 'sub2' in entry and 'sub1' not in entry:
                        ep_num = entry['episode']
                        # Check if we have a sub1 entry with this episode number
                        if ep_num in ep_only_map:
                            # Just use the first one if multiple matches (or could be more sophisticated)
                            sub1_key = ep_only_map[ep_num][0]
                            sub1_entry = episode_subs[sub1_key]
                            
                            # If sub1 entry doesn't already have a sub2, add it
                            if 'sub2' not in sub1_entry:
                                sub1_entry['sub2'] = entry['sub2']
                                self.logger.info(f"Matched by episode number only: {sub1_key} with {ep_key}")
                                matched_count += 1
                                
                                # Remove this episode from available episodes
                                ep_only_map[ep_num].remove(sub1_key)
                                if not ep_only_map[ep_num]:
                                    del ep_only_map[ep_num]
                
                if matched_count > 0:
                    self.logger.info(f"Successfully matched {matched_count} pairs by episode number only")
                    
                    # Refresh the matched_pairs list
                    matched_pairs = [k for k, v in episode_subs.items() if 'sub1' in v and 'sub2' in v]

            self.logger.info(f"Found {len(matched_pairs)} matched subtitle pairs")
            for pair in matched_pairs:
                sub1_name = episode_subs[pair]['sub1'].name
                sub2_name = episode_subs[pair]['sub2'].name if 'sub2' in episode_subs[pair] else "None"
                self.logger.debug(f"Matched pair for {pair}: sub1={sub1_name}, sub2={sub2_name}")

            if not matched_pairs:
                self.logger.error("No matched subtitle pairs found. Check your patterns or try automatic detection.")
                QMessageBox.warning(self, "No Matches", 
                                   "No matching subtitle pairs were found. Please check your patterns or try automatic detection.")
                return

            # Find and process video files - only look for MKV files
            video_files = [f for f in Path(video_dir).glob('**/*.mkv')]
            
            self.logger.info(f"Found {len(video_files)} video files")

            # Process each video file
            video_eps = self.find_episodes(video_files, sub2_ep_pattern)
            for video_file in video_files:
                self.logger.debug(f"Found video file: {video_file.name}")
                try:
                    ep_key = ''
                    for key, value in video_eps.items():
                        if value['file_name'] == video_file.name:
                            ep_key = key
                            break
                    self.logger.debug(f"Extracted {ep_key} from {video_file.name}")
                    
                    if ep_key not in episode_subs:
                        self.logger.warning(f"No subtitles found for {ep_key}")
                        continue
                    if 'sub2' not in episode_subs[ep_key]:
                        self.logger.warning(f"Missing sub2 for {ep_key}")
                        continue
                    
                    sub1_file = episode_subs[ep_key].get('sub1')
                    sub2_file = episode_subs[ep_key].get('sub2')
                    
                    if not sub1_file:
                        self.logger.warning(f"Missing sub1 for {ep_key}")
                        continue
                    
                    self.logger.debug(f"Processing {ep_key} with sub1={sub1_file.name}, sub2={sub2_file.name}")
                    
                    # Copy subtitle files next to video with consistent naming
                    try:
                        sub1_dest = video_file.parent / f'{video_file.stem}.sub1.srt'
                        sub2_dest = video_file.parent / f'{video_file.stem}.sub2.srt'
                        import shutil
                        shutil.copy2(sub1_file, sub1_dest)
                        shutil.copy2(sub2_file, sub2_dest)
                        self.logger.info(f"Copied subtitle files for {ep_key}")
                    except Exception as e:
                        self.logger.error(f"Error copying subtitle files for {ep_key}: {e}")
                        continue
                    
                    # Create merger instance for this episode
                    merger = Merger(
                        output_path=str(video_file.parent),
                        output_name=f'{video_file.stem}.merged.srt',
                        output_encoding=self.codec_combo.currentText()
                    )
                    
                    # Apply SVG filtering options
                    if hasattr(self, 'option_enable_svg_filtering'):
                        merger.enable_svg_filtering(self.option_enable_svg_filtering.isChecked())
                    
                    if hasattr(self, 'option_remove_text_entries'):
                        merger.set_remove_text_entries(self.option_remove_text_entries.isChecked())
                    
                    # Apply timing adjustments
                    sub1_delay = self.sub1_delay_spinner.value()
                    sub2_delay = self.sub2_delay_spinner.value()
                    
                    # Apply ALASS sync if enabled
                    if self.enable_alass_sync.isChecked():
                        self.sync_with_alass(sub1_dest, video_file)
                        self.sync_with_alass(sub2_dest, video_file)
                    
                    # Apply manual delay after ALASS (if any)
                    if sub1_delay != 0:
                        self.apply_subtitle_delay(sub1_dest, sub1_delay)
                    if sub2_delay != 0:
                        self.apply_subtitle_delay(sub2_dest, sub2_delay)
                    
                    # Add first subtitle (Japanese) with color and size
                    merger.add(
                        str(sub1_dest),  # Use the copied file
                        codec=self.codec_combo.currentText(),
                        color=self.color_combo.currentText(),
                        size=self.sub1_font_slider.value(),
                        bold=self.sub1_thickness_checkbox.isChecked(),
                        preserve_svg=self.option_preserve_svg.isChecked() if hasattr(self, 'option_preserve_svg') else True
                    )
                    
                    # Add second subtitle (non-Japanese)
                    merger.add(
                        str(sub2_dest),  # Use the copied file
                        codec=self.codec_combo.currentText(),
                        color=WHITE,
                        size=self.sub2_font_slider.value(),
                        bold=self.sub2_thickness_checkbox.isChecked(),
                        preserve_svg=self.option_preserve_svg.isChecked() if hasattr(self, 'option_preserve_svg') else True
                    )
                    
                    # Merge subtitles to create the merged SRT file
                    merger.merge()
                    merged_srt_path = merger.get_output_path()
                    self.logger.info(f"Successfully merged subtitles for {ep_key}")

                    # Generate ASS files if enabled
                    if hasattr(self, 'option_convert_to_ass') and self.option_convert_to_ass.isChecked():
                        try:
                            # Base style settings
                            base_style = {
                                'font': "MS Gothic",  # Japanese font
                                'font_size': self.sub1_font_slider.value(),
                                'ruby_font_size': self.sub1_font_slider.value() // 2,  # Half the size for ruby
                                'text_color': self.color_combo.currentText(),
                                'outline_size': 1.5,  # Thinner outline
                                'shadow_size': 0.5,  # Subtle shadow
                            }

                            # 1. Basic ASS with furigana
                            basic_ass_path = str(video_file.parent / f'{video_file.stem}.basic.ass')
                            create_ass_from_srt(
                                srt_file_path=merged_srt_path,
                                output_dir=str(video_file.parent),
                                auto_generate_furigana=True,
                                advanced_styling=False,
                                **base_style
                            )
                            self.logger.info(f"Created basic ASS with furigana for {ep_key}")

                            # 2. ASS with furigana and colors
                            color_ass_path = str(video_file.parent / f'{video_file.stem}.color.ass')
                            create_ass_from_srt(
                                srt_file_path=merged_srt_path,
                                output_dir=str(video_file.parent),
                                auto_generate_furigana=True,
                                advanced_styling=False,
                                use_colors=True,
                                **base_style
                            )
                            self.logger.info(f"Created colored ASS with furigana for {ep_key}")

                            # 3. ASS with advanced styling
                            advanced_ass_path = str(video_file.parent / f'{video_file.stem}.advanced.ass')
                            create_ass_from_srt(
                                srt_file_path=merged_srt_path,
                                output_dir=str(video_file.parent),
                                auto_generate_furigana=True,
                                advanced_styling=True,
                                use_colors=True,
                                **base_style
                            )
                            self.logger.info(f"Created advanced ASS with furigana for {ep_key}")

                        except Exception as e:
                            self.logger.error(f"Error creating ASS files for {ep_key}: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing video file {video_file}: {e}")
                    continue
            
            self.logger.info("Merge operation completed")
            QMessageBox.information(self, "Merge Complete", 
                                   f"Successfully processed {len(matched_pairs)} subtitle pairs.")
            
        except Exception as e:
            self.logger.error(f"Error during merge operation: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Error during merge operation: {str(e)}")

    def create_new_config_file(self, directory_path):
        """Create a new configuration file for the given directory."""
        try:
            # Generate unique config name based on directory
            dir_name = Path(directory_path).name
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            config_name = f"config_{dir_name.replace(' ', '_')}_{timestamp}.json"
            
            # Create new config with default values
            config = {
                'input_directory': directory_path,
                'video_directory': '',
                'sub1_pattern': r'\.JA\.srt$',  # Match Japanese subtitles
                'sub2_pattern': r'\.2\.fff\.srt$',  # Match English subtitles
                'sub1_ep_pattern': r'S01E(\d+)',  # Extract episode number after S01E
                'sub2_ep_pattern': r'- (\d+) \[',  # Extract episode number between - and [
                'sub1_font_size': 19,
                'sub2_font_size': 17,
                'sub1_color': 'Yellow',
                'sub2_color': 'White',
                'sub1_bold': False,
                'sub2_bold': False,
                'enable_svg_filtering': False,
                'remove_text_entries': False,
                'preserve_svg': True,
                'auto_detect_mode': False
            }
            
            # Save current settings to the new file
            self.save_settings(config)
            
            self.logger.info(f"Created new configuration file: {config_name}")
        except Exception as e:
            self.logger.error(f"Error creating new configuration file: {e}")

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
        try:
            if hasattr(self, 'batch_merge_button') and self.batch_merge_button:
                self.batch_merge_button.setEnabled(enabled)
                
            if hasattr(self, 'guess_patterns_btn') and self.guess_patterns_btn:
                self.guess_patterns_btn.setEnabled(enabled)
                
            if hasattr(self, 'auto_mode_toggle') and self.auto_mode_toggle:
                self.auto_mode_toggle.setEnabled(enabled)
                
            self.logger.debug(f"Controls {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error setting controls enabled state: {e}")
            else:
                print(f"Error setting controls enabled state: {e}")

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

    def guess_patterns(self):
        """Analyze subtitle files and suggest patterns."""
        input_dir = self.dir_entry.text()
        if not input_dir:
            self.logger.error("Please select an input directory first")
            return

        try:
            self.logger.info(f"Analyzing subtitle files in {input_dir}")
            # Disable UI during analysis
            self.set_controls_enabled(False)
            self.repaint()  # Force UI update
            
            # Get pattern suggestions
            result = suggest_patterns(input_dir, self.logger)
            
            if 'error' in result:
                self.logger.error(f"Error analyzing files: {result['error']}")
                self.set_controls_enabled(True)
                return
                
            patterns = result['suggested_patterns']
            verification = result['verification']
            
            # Update UI with suggested patterns
            if patterns['sub1_pattern']:
                self.sub1_pattern_entry.setText(patterns['sub1_pattern'])
            if patterns['sub2_pattern']:
                self.sub2_pattern_entry.setText(patterns['sub2_pattern'])
            if patterns['sub1_ep_pattern']:
                self.sub1_episode_pattern_entry.setText(patterns['sub1_ep_pattern'])
            if patterns['sub2_ep_pattern']:
                self.sub2_episode_pattern_entry.setText(patterns['sub2_ep_pattern'])
                
            # Log results
            self.logger.info(f"Pattern analysis complete")
            self.logger.info(f"File count: {result['file_count']}")
            
            # Log verification metrics safely with default values in case keys are missing
            self.logger.info(f"Sub1 pattern matches: {verification.get('sub1_matches', 0)}/{result['file_count']} files")
            self.logger.info(f"Sub2 pattern matches: {verification.get('sub2_matches', 0)}/{result['file_count']} files")
            self.logger.info(f"Overlapping matches: {verification.get('overlap', 0)}")
            
            sub1_matches = verification.get('sub1_matches', 0) or 1  # Avoid division by zero
            sub2_matches = verification.get('sub2_matches', 0) or 1  # Avoid division by zero
            
            self.logger.info(f"Sub1 episode extraction: {verification.get('sub1_ep_matches', 0)}/{sub1_matches} matches")
            self.logger.info(f"Sub2 episode extraction: {verification.get('sub2_ep_matches', 0)}/{sub2_matches} matches")
            
            # Log Japanese content detection
            if 'japanese_files' in result and result['japanese_files']:
                self.logger.info(f"Detected {len(result['japanese_files'])} files with significant Japanese content")
                self.logger.info(f"Japanese files: {', '.join(result['japanese_files'])}")
            
            # Show a message with the results
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Pattern Analysis Results")
            
            # Prepare message text
            message = f"Analysis complete for {result['file_count']} subtitle files.\n\n"
            message += f"Sub1 pattern: {patterns['sub1_pattern'] or 'None'}\n"
            message += f"Sub2 pattern: {patterns['sub2_pattern'] or 'None'}\n"
            message += f"Sub1 episode pattern: {patterns['sub1_ep_pattern'] or 'None'}\n"
            message += f"Sub2 episode pattern: {patterns['sub2_ep_pattern'] or 'None'}\n\n"
            
            message += f"Sub1 matches: {verification.get('sub1_matches', 0)}/{result['file_count']} files\n"
            message += f"Sub2 matches: {verification.get('sub2_matches', 0)}/{result['file_count']} files\n"
            message += f"Overlapping matches: {verification.get('overlap', 0)}\n\n"
            
            # Add Japanese content info
            if 'japanese_files' in result and result['japanese_files']:
                message += f"Japanese Content: Detected {len(result['japanese_files'])} files with >30% Japanese characters\n"
                
                # List the first few files (up to 5)
                if len(result['japanese_files']) <= 5:
                    message += f"Japanese files: {', '.join(result['japanese_files'])}\n\n"
                else:
                    message += f"Japanese files: {', '.join(result['japanese_files'][:5])} and {len(result['japanese_files']) - 5} more\n\n"
                
                # Show if patterns were based on Japanese content detection
                if 'groups' in result and 'Japanese_Content' in result['groups']:
                    message += "NOTE: Patterns were created based on Japanese content detection.\n\n"
            
            message += "Pattern suggestions have been applied to the UI fields."
            
            msg.setText(message)
            msg.exec()
            
        except Exception as e:
            self.logger.error(f"Error in guess_patterns: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.set_controls_enabled(True)

    def toggle_detection_mode(self):
        """Toggle between manual and automatic pattern detection modes."""
        self.auto_detect_mode = not self.auto_detect_mode
        self.set_detection_mode(self.auto_detect_mode)
        self.save_settings()
        
    def set_detection_mode(self, is_auto: bool):
        """Update UI based on detection mode."""
        try:
            self.auto_detect_mode = is_auto
            
            # Update toggle button text if it exists
            if hasattr(self, 'auto_mode_toggle') and self.auto_mode_toggle is not None:
                self.auto_mode_toggle.setChecked(is_auto)
                self.auto_mode_toggle.setText(f"{'Automatic' if is_auto else 'Manual'} Mode")
                
                # Update tooltip
                if is_auto:
                    self.auto_mode_toggle.setToolTip(
                        "Automatic mode: Patterns will be detected automatically based on file analysis.\n"
                        "Click to switch to manual mode."
                    )
                else:
                    self.auto_mode_toggle.setToolTip(
                        "Manual mode: Use custom patterns for subtitle files.\n"
                        "Click to switch to automatic mode."
                    )
                
            # Toggle visibility of pattern entry fields if they exist
            if hasattr(self, 'pattern_widgets_container') and self.pattern_widgets_container is not None:
                self.pattern_widgets_container.setVisible(not is_auto)
                    
            # Log the change
            if hasattr(self, 'logger'):
                self.logger.info(f"Detection mode set to: {'Automatic' if is_auto else 'Manual'}")
                
            # Save the setting
            if hasattr(self, 'settings'):
                self.settings['auto_detect_mode'] = is_auto
                self.save_settings()
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error setting detection mode: {e}")
            else:
                print(f"Error setting detection mode: {e}")

    def update_toggle_button_text(self):
        """Update the toggle button text based on the current mode."""
        self.auto_mode_toggle.setText(f"{'Automatic' if self.auto_detect_mode else 'Manual'} Mode")

    def load_settings(self):
        """Load saved settings."""
        # Initialize settings if not already done
        if not hasattr(self, 'settings'):
            # First call BaseTab's load_settings to get default settings
            try:
                self.settings = super().load_settings()
                if self.settings is None:
                    self.logger.error("Failed to load default settings")
                    self.settings = {}
            except Exception as e:
                self.logger.error(f"Error loading default settings: {e}")
                self.settings = {}
        
        # Load auto detection mode
        self.auto_detect_mode = self.settings.get('auto_detect_mode', False)
        self.logger.debug(f"Loaded auto_detect_mode: {self.auto_detect_mode}")
        
        return self.settings

    def save_settings(self, settings=None):
        """Save current settings."""
        try:
            # First call the parent class's save_settings to handle common settings
            super().save_settings(settings)
            
            # Now handle directory tab specific settings
            if hasattr(self, 'settings'):
                # Save auto detection mode
                self.settings['auto_detect_mode'] = self.auto_detect_mode
                print(f"Auto detection mode: {self.auto_detect_mode}")
                print(f"Has sub1_pattern_entry: {hasattr(self, 'sub1_pattern_entry')}")
                print(f"Has sub2_pattern_entry: {hasattr(self, 'sub2_pattern_entry')}")
                print(f"Has sub1_episode_pattern_entry: {hasattr(self, 'sub1_episode_pattern_entry')}")
                print(f"Has sub2_episode_pattern_entry: {hasattr(self, 'sub2_episode_pattern_entry')}")
                print(f"Has sub1_pattern: {hasattr(self, 'sub1_pattern')}")
                print(f"Has sub2_pattern: {hasattr(self, 'sub2_pattern')}")
                print(f"Has sub1_episode_pattern: {hasattr(self, 'sub1_episode_pattern')}")
                print(f"Has sub2_episode_pattern: {hasattr(self, 'sub2_episode_pattern')}")
                # Save file patterns if they exist
                if self.sub1_pattern_entry is not None:
                    self.settings['sub1_pattern'] = self.sub1_pattern_entry.text()
                if self.sub2_pattern_entry is not None:
                    self.settings['sub2_pattern'] = self.sub2_pattern_entry.text()
                if self.sub1_episode_pattern_entry is not None:
                    self.settings['sub1_episode_pattern'] = self.sub1_episode_pattern_entry.text()
                if self.sub2_episode_pattern_entry is not None:
                    self.settings['sub2_episode_pattern'] = self.sub2_episode_pattern_entry.text()
                # font size
                if self.font_size_spinbox is not None:
                    self.settings['font_size'] = self.font_size_spinbox.value()
                # Update with additional settings if provided
                if settings:
                    self.settings.update(settings)
                
                # Save to file
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4)
                
                self.logger.info("Directory tab settings saved")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def update_ui_from_settings(self):
        """Update UI elements based on loaded settings."""
        # Update auto detection mode UI
        if hasattr(self, 'auto_mode_toggle'):
            self.set_detection_mode(self.auto_detect_mode)
        
        # Update pattern entries if they exist
        if hasattr(self, 'sub1_pattern_entry'):
            self.sub1_pattern_entry.setText(self.settings.get('sub1_pattern', ''))
        if hasattr(self, 'sub2_pattern_entry'):
            self.sub2_pattern_entry.setText(self.settings.get('sub2_pattern', ''))
        if hasattr(self, 'sub1_episode_pattern_entry'):
            self.sub1_episode_pattern_entry.setText(self.settings.get('sub1_episode_pattern', ''))
        if hasattr(self, 'sub2_episode_pattern_entry'):
            self.sub2_episode_pattern_entry.setText(self.settings.get('sub2_episode_pattern', ''))
        # font size
        if hasattr(self, 'font_size_spinbox'):
            self.font_size_spinbox.setValue(self.settings.get('font_size', 30))
            
        self.logger.debug("UI updated from settings")

    def toggle_alass_settings(self):
        """Enable or disable ALASS settings based on checkbox state"""
        if hasattr(self, 'alass_path_entry') and self.alass_path_entry is not None:
            enabled = self.enable_alass_sync.isChecked() if hasattr(self, 'enable_alass_sync') else False
            self.alass_path_entry.setEnabled(enabled)
            self.save_value_to_settings('enable_alass_sync', enabled)

    def browse_alass_path(self):
        """Browse for ALASS executable"""
        file_filter = ""
        if sys.platform == 'win32':
            file_filter = "Executable files (*.exe);;All files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select ALASS Executable", 
            self.alass_path_entry.text() or str(Path.home()),
            file_filter
        )
        
        if file_path:
            self.alass_path_entry.setText(file_path)
            self.save_value_to_settings('alass_path', file_path)

    def apply_subtitle_delay(self, subtitle_path: Path, delay_ms: int) -> bool:
        """
        Apply a time delay to a subtitle file.
        
        Args:
            subtitle_path: Path to the subtitle file
            delay_ms: Delay in milliseconds (positive = delay, negative = advance)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if delay_ms == 0:
            return True  # No delay needed
            
        try:
            self.logger.info(f"Applying {delay_ms}ms delay to {subtitle_path.name}")
            
            # Read the subtitle file
            with open(subtitle_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Time format in SRT: 00:00:00,000 --> 00:00:00,000
            time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})')
            
            def adjust_time(match):
                # Convert all time components to milliseconds
                parts = [int(g) for g in match.groups()]
                start_ms = ((parts[0] * 60 + parts[1]) * 60 + parts[2]) * 1000 + parts[3]
                end_ms = ((parts[4] * 60 + parts[5]) * 60 + parts[6]) * 1000 + parts[7]
                
                # Apply delay
                start_ms += delay_ms
                end_ms += delay_ms
                
                # Ensure times don't go negative
                start_ms = max(0, start_ms)
                end_ms = max(0, end_ms)
                
                # Convert back to SRT format
                start_h = start_ms // 3600000
                start_ms %= 3600000
                start_m = start_ms // 60000
                start_ms %= 60000
                start_s = start_ms // 1000
                start_ms %= 1000
                
                end_h = end_ms // 3600000
                end_ms %= 3600000
                end_m = end_ms // 60000
                end_ms %= 60000
                end_s = end_ms // 1000
                end_ms %= 1000
                
                return f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> {end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}"
            
            # Apply regex substitution
            adjusted_content = time_pattern.sub(adjust_time, content)
            
            # Write adjusted content back to file
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(adjusted_content)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying delay to {subtitle_path}: {e}")
            return False

    def sync_with_alass(self, subtitle_path: Path, video_path: Path) -> bool:
        """
        Synchronize a subtitle file with a video file using ALASS.
        
        Args:
            subtitle_path: Path to the subtitle file
            video_path: Path to the video file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enable_alass_sync.isChecked():
            return True  # ALASS sync not enabled
            
        try:
            # Check if ALASS is available
            alass_path = self.settings.get('alass_path', '')
            
            # If no specific path, try using 'alass' command directly (assuming it's in PATH)
            if not alass_path:
                if sys.platform == 'win32':
                    alass_path = 'alass.exe'
                else:
                    alass_path = 'alass'
            
            self.logger.info(f"Synchronizing {subtitle_path.name} with {video_path.name} using ALASS")
            
            # Create temp file for synchronized output
            temp_output = subtitle_path.with_name(f"{subtitle_path.stem}.synced{subtitle_path.suffix}")
            
            # Build ALASS command
            cmd = [
                alass_path,
                str(video_path),  # Reference video
                str(subtitle_path),  # Input subtitle
                str(temp_output)  # Output subtitle
            ]
            
            # Run ALASS
            self.logger.debug(f"Running ALASS command: {' '.join(cmd)}")
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Check result
            if process.returncode == 0 and temp_output.exists():
                # Replace original with synchronized version
                temp_output.replace(subtitle_path)
                self.logger.info(f"Successfully synchronized {subtitle_path.name}")
                return True
            else:
                self.logger.error(f"ALASS failed: {process.stderr}")
                if temp_output.exists():
                    temp_output.unlink()  # Delete temp file
                return False
                
        except Exception as e:
            self.logger.error(f"Error using ALASS to synchronize {subtitle_path}: {e}")
            return False

    def save_value_to_settings(self, key: str, value):
        """Save a value to the settings."""
        try:
            print(f"Saving {key} to settings: {value}")
            if hasattr(self, 'settings'):
                self.settings[key] = value
                print(f"Settings: {self.settings}")
                self.save_settings()
        except Exception as e:
            self.logger.error(f"Error saving value to settings: {e}")