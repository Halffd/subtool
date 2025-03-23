#!/usr/bin/env python
# Merge Subtitles - Merges the star subtitle with the example subtitle

import os
import sys
from pathlib import Path

# Add src directory to path to import modules
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

try:
    from utils.merger import Merger, WHITE, YELLOW
except ImportError:
    print("Error: Could not import merger module. Make sure you have the correct directory structure.")
    sys.exit(1)

def main():
    """Merge the star subtitle with the example subtitle."""
    print("Merging subtitles...")
    
    # Define paths
    star_subtitle_path = "star_subtitle.srt"
    example_subtitle_path = "example_subtitle.srt"
    merged_subtitle_path = "merged_subtitle.srt"
    
    # Check if files exist
    if not os.path.exists(star_subtitle_path):
        print(f"Error: {star_subtitle_path} does not exist. Run create_star_srt.py first.")
        return
    
    if not os.path.exists(example_subtitle_path):
        print(f"Error: {example_subtitle_path} does not exist.")
        return
    
    # Create merger
    merger = Merger(
        output_path=".",
        output_name=merged_subtitle_path,
        output_encoding='utf-8'
    )
    
    # Add star subtitle
    print(f"Adding star subtitle: {star_subtitle_path}")
    merger.add(
        subtitle_address=star_subtitle_path,
        codec='utf-8',
        color=WHITE,
        size=None,
        top=False,  # Position is already set in the SVG subtitle
        bold=False,
        preserve_svg=True  # Important: preserve SVG paths
    )
    
    # Add example subtitle
    print(f"Adding example subtitle: {example_subtitle_path}")
    merger.add(
        subtitle_address=example_subtitle_path,
        codec='utf-8',
        color=YELLOW,
        size=24,
        top=False,
        bold=True,
        preserve_svg=True
    )
    
    # Merge subtitles
    merger.merge()
    
    print(f"Merged subtitle saved to: {merged_subtitle_path}")
    print("\nYou can now use this subtitle file with MPV player:")
    print(f"mpv --sub-file={merged_subtitle_path} your_video_file.mp4")

if __name__ == "__main__":
    main() 