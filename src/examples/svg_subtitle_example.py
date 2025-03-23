#!/usr/bin/env python
# SVG Subtitle Example - Demonstrates how to create and merge subtitle files with SVG path data

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.merger import Merger, WHITE, YELLOW
from utils.create_svg_subtitle import create_svg_subtitle

def main():
    """Main function to demonstrate SVG subtitle creation and merging."""
    print("SVG Subtitle Example")
    print("===================")
    
    # Create temporary directory for output files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define paths
        svg_subtitle_path = os.path.join(temp_dir, "svg_subtitle.srt")
        regular_subtitle_path = os.path.join(temp_dir, "regular_subtitle.srt")
        merged_subtitle_path = os.path.join(temp_dir, "merged_subtitle.srt")
        
        # SVG path data (star shape)
        svg_path = "m 88.00 0.00 b 91.58 3.63 92.38 7.36 94.35 12.00 94.35 12.00 104.19 38.00 104.19 38.00 105.40 41.75 107.85 51.10 110.47 53.42 112.89 55.55 119.75 56.63 123.00 57.13 123.00 57.13 144.00 61.42 144.00 61.42 144.00 61.42 160.98 65.44 160.98 65.44 163.07 66.02 166.06 66.93 164.83 69.77 163.99 71.71 158.45 76.10 156.58 77.74 146.95 86.16 144.87 87.25 135.00 94.42 132.18 96.48 124.55 102.37 123.02 105.17 121.16 108.57 123.33 118.07 123.78 122.28 123.78 122.28 126.98 153.00 126.98 153.00 126.98 153.00 126.98 163.00 126.98 163.00 118.18 159.97 100.44 146.94 92.00 141.46 88.48 139.17 80.85 132.80 77.00 132.66 74.37 132.57 65.04 137.36 62.00 138.67 49.93 143.89 37.07 151.98 24.00 154.00 25.09 141.84 30.16 125.80 33.72 114.00 34.81 110.39 38.85 101.20 37.78 98.00 36.50 94.13 27.27 86.08 24.00 82.83 18.92 77.78 3.29 58.99 1.00 53.00 1.00 53.00 35.00 50.87 35.00 50.87 35.00 50.87 49.00 50.87 49.00 50.87 51.80 51.00 55.39 51.21 57.90 49.83 62.52 47.27 68.04 33.08 70.67 28.00 70.67 28.00 88.00 0.00 88.00 0.00"
        
        # Create SVG subtitle file
        svg_subtitle_content = create_svg_subtitle(
            svg_path=svg_path,
            start_time="00:02:00,540",
            end_time="00:02:03,430",
            position=9,  # top-right
            font_face="Brady Bunch Remastered",
            font_size=48,
            color="#FFFFFF"
        )
        
        with open(svg_subtitle_path, 'w', encoding='utf-8') as f:
            f.write(svg_subtitle_content)
        
        print(f"Created SVG subtitle file: {svg_subtitle_path}")
        
        # Create regular subtitle file
        regular_subtitle_content = """1
00:02:00,540 --> 00:02:03,430
This is a regular subtitle.

2
00:02:05,000 --> 00:02:08,000
Another regular subtitle.

"""
        
        with open(regular_subtitle_path, 'w', encoding='utf-8') as f:
            f.write(regular_subtitle_content)
        
        print(f"Created regular subtitle file: {regular_subtitle_path}")
        
        # Create merger
        merger = Merger(
            output_path=temp_dir,
            output_name="merged_subtitle.srt",
            output_encoding='utf-8'
        )
        
        # Add SVG subtitle
        merger.add(
            subtitle_address=svg_subtitle_path,
            codec='utf-8',
            color=WHITE,
            size=None,
            top=False,  # Position is already set in the SVG subtitle
            bold=False,
            preserve_svg=True  # Important: preserve SVG paths
        )
        
        # Add regular subtitle
        merger.add(
            subtitle_address=regular_subtitle_path,
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
        
        # Copy merged subtitle to current directory for easy access
        current_dir_output = "merged_subtitle.srt"
        with open(merged_subtitle_path, 'r', encoding='utf-8') as f_in:
            with open(current_dir_output, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
        
        print(f"Copied merged subtitle to current directory: {current_dir_output}")
        print("\nYou can now use this subtitle file with MPV player:")
        print(f"mpv --sub-file={current_dir_output} your_video_file.mp4")

if __name__ == "__main__":
    main() 