#!/usr/bin/env python
# Create Star SRT - Creates an SRT file with the star SVG path data

import os
import sys

def main():
    """Create an SRT file with the star SVG path data."""
    print("Creating star subtitle file...")
    
    # Define output path
    output_path = "star_subtitle.srt"
    
    # Star SVG path data
    star_path = "m 88.00 0.00 b 91.58 3.63 92.38 7.36 94.35 12.00 94.35 12.00 104.19 38.00 104.19 38.00 105.40 41.75 107.85 51.10 110.47 53.42 112.89 55.55 119.75 56.63 123.00 57.13 123.00 57.13 144.00 61.42 144.00 61.42 144.00 61.42 160.98 65.44 160.98 65.44 163.07 66.02 166.06 66.93 164.83 69.77 163.99 71.71 158.45 76.10 156.58 77.74 146.95 86.16 144.87 87.25 135.00 94.42 132.18 96.48 124.55 102.37 123.02 105.17 121.16 108.57 123.33 118.07 123.78 122.28 123.78 122.28 126.98 153.00 126.98 153.00 126.98 153.00 126.98 163.00 126.98 163.00 118.18 159.97 100.44 146.94 92.00 141.46 88.48 139.17 80.85 132.80 77.00 132.66 74.37 132.57 65.04 137.36 62.00 138.67 49.93 143.89 37.07 151.98 24.00 154.00 25.09 141.84 30.16 125.80 33.72 114.00 34.81 110.39 38.85 101.20 37.78 98.00 36.50 94.13 27.27 86.08 24.00 82.83 18.92 77.78 3.29 58.99 1.00 53.00 1.00 53.00 35.00 50.87 35.00 50.87 35.00 50.87 49.00 50.87 49.00 50.87 51.80 51.00 55.39 51.21 57.90 49.83 62.52 47.27 68.04 33.08 70.67 28.00 70.67 28.00 88.00 0.00 88.00 0.00"
    
    # Create subtitle content
    subtitle_content = f"""1
00:02:00,540 --> 00:02:03,430
<font face="Brady Bunch Remastered" size="48" color="#FFFFFF">{{\\an9}}{star_path}</font>

"""
    
    # Write subtitle file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(subtitle_content)
    
    print(f"Created star subtitle file: {output_path}")
    print("\nYou can now use this subtitle file with MPV player:")
    print(f"mpv --sub-file={output_path} your_video_file.mp4")

if __name__ == "__main__":
    main() 