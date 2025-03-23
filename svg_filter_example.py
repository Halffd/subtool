#!/usr/bin/env python
# SVG Filter Example - Demonstrates how to use the SVG filtering functionality

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
    """Demonstrate SVG filtering functionality."""
    print("SVG Filtering Example")
    print("====================")
    
    # Define paths
    example_stars_path = "example_stars.srt"
    output_dir = "."
    
    # Check if example file exists
    if not os.path.exists(example_stars_path):
        print(f"Error: {example_stars_path} does not exist.")
        print("Please run the script in the same directory as example_stars.srt.")
        return
    
    # Example 1: Basic merge with SVG filtering
    print("\nExample 1: Basic merge with SVG filtering")
    print("----------------------------------------")
    
    # Create merger with SVG filtering enabled
    merger1 = Merger(
        output_path=output_dir,
        output_name="filtered_stars.srt",
        output_encoding='utf-8'
    )
    
    # Enable SVG filtering
    merger1.enable_svg_filtering(True)
    
    # Add subtitle file
    print(f"Adding subtitle file: {example_stars_path}")
    merger1.add(
        subtitle_address=example_stars_path,
        codec='utf-8',
        color=WHITE,
        preserve_svg=True  # Important: preserve SVG paths
    )
    
    # Merge subtitles
    merger1.merge()
    
    print(f"Filtered subtitle saved to: {os.path.join(output_dir, 'filtered_stars.srt')}")
    
    # Example 2: Merge with SVG filtering and text removal
    print("\nExample 2: Merge with SVG filtering and text removal")
    print("--------------------------------------------------")
    
    # Create merger with SVG filtering enabled and text removal
    merger2 = Merger(
        output_path=output_dir,
        output_name="svg_only_stars.srt",
        output_encoding='utf-8'
    )
    
    # Enable SVG filtering and text removal
    merger2.enable_svg_filtering(True)
    merger2.set_remove_text_entries(True)
    
    # Add subtitle file
    print(f"Adding subtitle file: {example_stars_path}")
    merger2.add(
        subtitle_address=example_stars_path,
        codec='utf-8',
        color=WHITE,
        preserve_svg=True  # Important: preserve SVG paths
    )
    
    # Merge subtitles
    merger2.merge()
    
    print(f"SVG-only subtitle saved to: {os.path.join(output_dir, 'svg_only_stars.srt')}")
    
    # Example 3: Merge with another subtitle file
    print("\nExample 3: Merge with another subtitle file")
    print("----------------------------------------")
    
    # Check if example subtitle file exists
    example_subtitle_path = "example_subtitle.srt"
    if not os.path.exists(example_subtitle_path):
        print(f"Warning: {example_subtitle_path} does not exist. Skipping Example 3.")
        return
    
    # Create merger with SVG filtering enabled
    merger3 = Merger(
        output_path=output_dir,
        output_name="merged_with_filtering.srt",
        output_encoding='utf-8'
    )
    
    # Enable SVG filtering
    merger3.enable_svg_filtering(True)
    
    # Add SVG subtitle file
    print(f"Adding SVG subtitle file: {example_stars_path}")
    merger3.add(
        subtitle_address=example_stars_path,
        codec='utf-8',
        color=WHITE,
        preserve_svg=True  # Important: preserve SVG paths
    )
    
    # Add regular subtitle file
    print(f"Adding regular subtitle file: {example_subtitle_path}")
    merger3.add(
        subtitle_address=example_subtitle_path,
        codec='utf-8',
        color=YELLOW,
        size=24,
        bold=True,
        preserve_svg=True
    )
    
    # Merge subtitles
    merger3.merge()
    
    print(f"Merged subtitle with filtering saved to: {os.path.join(output_dir, 'merged_with_filtering.srt')}")
    
    print("\nYou can now use these subtitle files with MPV player:")
    print(f"mpv --sub-file=filtered_stars.srt your_video_file.mp4")
    print(f"mpv --sub-file=svg_only_stars.srt your_video_file.mp4")
    print(f"mpv --sub-file=merged_with_filtering.srt your_video_file.mp4")
    
    print("\nSVG Filtering Options:")
    print("1. Enable SVG filtering: merger.enable_svg_filtering(True)")
    print("2. Remove text entries: merger.set_remove_text_entries(True)")
    print("3. Preserve SVG paths: add(..., preserve_svg=True)")

if __name__ == "__main__":
    main() 