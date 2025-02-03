"""Settings management utilities."""

import json
from pathlib import Path
from typing import Dict, Any

DEFAULT_SETTINGS = {
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
    'sub1_pattern': r'\[Some-Stuffs\]_Pocket_Monsters_\(2019\)_\d+.*(?<!Clean)\.srt$',
    'sub2_pattern': r'\[Some-Stuffs\]_Pocket_Monsters_\(2019\)_\d+.*-Clean\.srt$',
    'sub1_episode_pattern': r'_(\d{3})_',
    'sub2_episode_pattern': r'_(\d{3})_',
    'episode_pattern': r'\d+',
    'use_alass': False,
    'disable_fps_guessing': False,
    'alass_interval': 100,
    'alass_split_penalty': 10,
    'alass_sub_fps': 23.976,
    'alass_ref_fps': 23.976
}

class Settings:
    """Settings manager class."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.settings_file = config_dir / 'configs.json'
        self.settings = self.load()

    def load(self) -> Dict[str, Any]:
        """Load settings from file or create with defaults."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with defaults in case new settings were added
                    return {**DEFAULT_SETTINGS, **settings}
            else:
                self.save(DEFAULT_SETTINGS)
                return DEFAULT_SETTINGS
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS

    def save(self, settings: Dict[str, Any] = None):
        """Save settings to file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)
            
            # Update settings if provided
            if settings:
                self.settings.update(settings)
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
                
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save() 