"""Subtitle merging utilities."""

import pysrt
from pathlib import Path
from typing import List, Dict, Optional
from ..components.style import COLORS

class SubtitleMerger:
    """Class for merging multiple SRT files."""
    
    def __init__(self):
        self.subtitles: Dict[str, pysrt.SubRipFile] = {}
        self.colors: Dict[str, str] = {}
        self._color_index = 0
    
    def add_file(self, file_path: str, color: Optional[str] = None) -> None:
        """Add a subtitle file to be merged.
        
        Args:
            file_path: P
            ath to the SRT file
            color: Optional color for the subtitles (if None, will be assigned automatically)
        """
        try:
            subs = pysrt.open(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encodings if UTF-8 fails
            for encoding in ['windows-1252', 'latin-1', 'cp1251', 'windows-1256']:
                try:
                    subs = pysrt.open(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode file {file_path} with any known encoding")
        
        file_name = Path(file_path).stem
        self.subtitles[file_name] = subs
        
        # Assign color
        if color and color.upper() in COLORS:
            self.colors[file_name] = COLORS[color.upper()]
        else:
            # Cycle through available colors
            available_colors = list(COLORS.values())
            self.colors[file_name] = available_colors[self._color_index % len(available_colors)]
            self._color_index += 1
    
    def merge(self, output_path: str) -> None:
        """Merge all added subtitle files into a single output file.
        
        Args:
            output_path: Path where the merged SRT file will be saved
        """
        if not self.subtitles:
            raise ValueError("No subtitle files have been added")
        
        merged = pysrt.SubRipFile()
        
        # Merge all subtitles
        for file_name, subs in self.subtitles.items():
            color = self.colors[file_name]
            for sub in subs:
                # Create a new subtitle with colored text
                new_sub = pysrt.SubRipItem(
                    index=len(merged) + 1,
                    start=sub.start,
                    end=sub.end,
                    text=f'<font color="{color}">{sub.text}</font>'
                )
                merged.append(new_sub)
        
        # Sort by start time
        merged.sort(key=lambda x: x.start)
        
        # Fix indices
        for i, sub in enumerate(merged, 1):
            sub.index = i
        
        # Save merged file
        merged.save(output_path, encoding='utf-8')

def merge_directory(input_dir: str, output_dir: str, pattern: str) -> None:
    """Merge subtitle files in a directory based on a pattern.
    
    Args:
        input_dir: Directory containing subtitle files
        output_dir: Directory where merged files will be saved
        pattern: File pattern (e.g., "*_en.srt, *_fr.srt")
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Parse patterns
    patterns = [p.strip() for p in pattern.split(',')]
    if not patterns:
        raise ValueError("No valid patterns provided")
    
    # Group files by base name (without language suffix)
    groups: Dict[str, List[str]] = {}
    for pattern in patterns:
        for file_path in input_path.glob(pattern):
            # Get base name (e.g., "movie" from "movie_en.srt")
            base_name = file_path.stem.split('_')[0]
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(str(file_path))
    
    if not groups:
        raise ValueError(f"No files found matching patterns: {pattern}")
    
    # Process each group
    for base_name, files in groups.items():
        if len(files) < 2:
            continue  # Skip groups with only one subtitle file
        
        merger = SubtitleMerger()
        for file_path in files:
            merger.add_file(file_path)
        
        output_file = output_path / f"{base_name}_merged.srt"
        merger.merge(str(output_file)) 