import re
import shutil
import subprocess
from pathlib import Path
import datetime
from typing import List
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QMessageBox, QFileDialog
)
from .base_tab import BaseTab
from ..utils.merger import Merger, WHITE
from ..utils.ass_converter import create_ass_from_srt, process_directory as process_ass_directory

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

            def extract_episode_info(filename: str, primary_pattern: str = None) -> tuple[str, str]:
                """
                Extract season and episode numbers using multiple pattern attempts.
                Returns (season_num, episode_num) or (None, None) if no match found.
                """
                # Check if filename contains "E" pattern
                has_e_pattern = 'E' in filename.upper()
                
                # Try user-provided pattern first if available
                if primary_pattern:
                    try:
                        match = re.search(primary_pattern, filename)
                        if match:
                            # Assume it's just episode number if one group
                            if len(match.groups()) == 1:
                                # If filename has "E" pattern but pattern doesn't capture season, try to find it
                                if has_e_pattern:
                                    season_match = re.search(r'S(\d+)', filename)
                                    season_num = season_match.group(1) if season_match else '1'
                                    return season_num, match.group(1)
                                return '1', match.group(1)
                            # Assume season and episode if two groups
                            elif len(match.groups()) == 2:
                                return match.group(1), match.group(2)
                    except re.error:
                        self.logger.warning(f"Invalid user pattern: {primary_pattern}")

                # List of patterns to try, in order of preference
                patterns = [
                    # Standard season/episode format
                    (r'S(\d+)E(\d+)', lambda m: (m.group(1), m.group(2))),
                    # Season and episode separated
                    (r'S(\d+)[^E]*?(\d{2,3})', lambda m: (m.group(1), m.group(2))),
                ]

                # If filename has "E" pattern, only use patterns that extract season numbers
                if not has_e_pattern:
                    # Add fallback patterns only if no "E" in filename
                    patterns.extend([
                        # Just episode number with optional season
                        (r'(?:S(\d+)|S)?.*?(\d{2,3})', lambda m: (m.group(1) or '1', m.group(2))),
                        # Any number sequence as last resort
                        (r'(\d{2,3})', lambda m: ('1', m.group(1)))
                    ])

                # Try each pattern in sequence
                for pattern, extractor in patterns:
                    match = re.search(pattern, filename)
                    if match:
                        try:
                            return extractor(match)
                        except Exception:
                            continue

                return None, None
            
            # Find subtitle files (case insensitive)
            try:
                input_path = Path(input_dir)
                video_path = Path(video_dir)
                
                # List all srt files for logging
                all_srt_files = list(input_path.glob('*.srt'))
                self.logger.debug(f"Found {len(all_srt_files)} total .srt files")
                for srt_file in all_srt_files:
                    self.logger.debug(f"Found SRT file: {srt_file.name}")
                
                # First find sub1 files
                sub1_files = [f for f in all_srt_files 
                            if re.search(sub1_pattern, f.name, re.IGNORECASE)]
                
                # Then find sub2 files, excluding any that matched sub1
                sub2_files = [f for f in all_srt_files
                            if re.search(sub2_pattern, f.name, re.IGNORECASE) 
                            and f not in sub1_files]
                
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
                    season_num, ep_num = extract_episode_info(sub1.stem, sub1_ep_pattern)
                    
                    if season_num is not None and ep_num is not None:
                        # Create a unique key combining season and episode
                        ep_key = f"S{season_num}E{ep_num}"
                        
                        if ep_key not in episode_subs:
                            episode_subs[ep_key] = {
                                'sub1': sub1, 
                                'season': season_num, 
                                'episode': ep_num,
                                'has_e_pattern': 'E' in sub1.stem.upper()
                            }
                            self.logger.debug(f"Found sub1 for {ep_key}: {sub1.name}")
                        else:
                            self.logger.warning(f"Duplicate sub1 for {ep_key}: {sub1.name}")
                    else:
                        self.logger.warning(f"Could not extract episode info from sub1 file: {sub1.name}")
                except Exception as e:
                    self.logger.error(f"Error processing sub1 file {sub1}: {e}")
            
            # Process sub2 files
            for sub2 in sub2_files:
                try:
                    season_num, ep_num = extract_episode_info(sub2.stem, sub2_ep_pattern)
                    
                    if season_num is not None and ep_num is not None:
                        ep_key = f"S{season_num}E{ep_num}"
                        
                        if ep_key in episode_subs:
                            # If either file has E pattern, require season numbers to match
                            if (episode_subs[ep_key].get('has_e_pattern', False) or 
                                'E' in sub2.stem.upper()):
                                if episode_subs[ep_key]['season'] != season_num:
                                    self.logger.warning(
                                        f"Season number mismatch for {ep_key}: "
                                        f"sub1 season={episode_subs[ep_key]['season']}, "
                                        f"sub2 season={season_num}"
                                    )
                                    continue
                            episode_subs[ep_key]['sub2'] = sub2
                            self.logger.debug(f"Found sub2 for {ep_key}: {sub2.name}")
                        else:
                            episode_subs[ep_key] = {
                                'sub2': sub2, 
                                'season': season_num, 
                                'episode': ep_num,
                                'has_e_pattern': 'E' in sub2.stem.upper()
                            }
                            self.logger.warning(f"Found sub2 but no sub1 for {ep_key}: {sub2.name}")
                    else:
                        self.logger.warning(f"Could not extract episode info from sub2 file: {sub2.name}")
                except Exception as e:
                    self.logger.error(f"Error processing sub2 file {sub2}: {e}")

            # Find and process video files - only look for MKV files
            video_files = [f for f in Path(video_dir).glob('**/*.mkv')]
            
            self.logger.info(f"Found {len(video_files)} video files")

            # Process each video file
            for video_file in video_files:
                self.logger.debug(f"Found video file: {video_file.name}")
                try:
                    season_num, ep_num = extract_episode_info(video_file.stem)
                    
                    if season_num is None or ep_num is None:
                        self.logger.warning(f"Could not extract episode info from {video_file.name}")
                        continue
                    
                    ep_key = f"S{season_num}E{ep_num}"
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
                    
                    # Add first subtitle with color and size
                    merger.add(
                        str(sub1_dest),  # Use the copied file
                        codec=self.codec_combo.currentText(),
                        color=self.color_combo.currentText(),
                        size=self.sub1_font_slider.value(),
                        bold=self.sub1_thickness_checkbox.isChecked()
                    )
                    
                    # Add second subtitle
                    merger.add(
                        str(sub2_dest),  # Use the copied file
                        codec=self.codec_combo.currentText(),
                        color=WHITE,
                        size=self.sub2_font_slider.value(),
                        bold=self.sub2_thickness_checkbox.isChecked()
                    )
                    
                    # Merge subtitles to create the merged SRT file
                    merger.merge()
                    merged_srt_path = merger.get_output_path()
                    self.logger.info(f"Successfully merged subtitles for {ep_key}")

                    # Generate ASS files if enabled
                    if self.option_convert_to_ass.isChecked():
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
            
        except Exception as e:
            self.logger.error(f"Error during merge operation: {e}")

    def create_new_config_file(self, directory_path):
        """Create a new configuration file with the basename of the directory and date."""
        try:
            # Get the basename of the directory
            dir_basename = Path(directory_path).name
            
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

