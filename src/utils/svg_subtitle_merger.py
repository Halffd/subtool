#!/usr/bin/env python
# SVG Subtitle Merger - A tool to merge subtitles with SVG path data

import os
import sys
import argparse
from pathlib import Path
from .merger import Merger, WHITE, YELLOW, RED, BLUE, GREEN

def main():
    """Main function to handle command line arguments and merge subtitles."""
    parser = argparse.ArgumentParser(description='Merge subtitle files with SVG path support')
    
    parser.add_argument('--output', '-o', type=str, default='merged.srt',
                        help='Output file name (default: merged.srt)')
    parser.add_argument('--output-dir', '-d', type=str, default='.',
                        help='Output directory (default: current directory)')
    parser.add_argument('--encoding', '-e', type=str, default='utf-8',
                        help='Output file encoding (default: utf-8)')
    
    # First subtitle file arguments
    parser.add_argument('--sub1', type=str, required=True,
                        help='First subtitle file path')
    parser.add_argument('--sub1-color', type=str, default='white',
                        help='Color for first subtitle (default: white)')
    parser.add_argument('--sub1-size', type=int, default=None,
                        help='Font size for first subtitle')
    parser.add_argument('--sub1-top', action='store_true',
                        help='Position first subtitle at top of screen')
    parser.add_argument('--sub1-bold', action='store_true',
                        help='Make first subtitle bold')
    parser.add_argument('--sub1-codec', type=str, default='utf-8',
                        help='Encoding for first subtitle file (default: utf-8)')
    
    # Second subtitle file arguments
    parser.add_argument('--sub2', type=str, required=False,
                        help='Second subtitle file path')
    parser.add_argument('--sub2-color', type=str, default='yellow',
                        help='Color for second subtitle (default: yellow)')
    parser.add_argument('--sub2-size', type=int, default=None,
                        help='Font size for second subtitle')
    parser.add_argument('--sub2-top', action='store_true',
                        help='Position second subtitle at top of screen')
    parser.add_argument('--sub2-bold', action='store_true',
                        help='Make second subtitle bold')
    parser.add_argument('--sub2-codec', type=str, default='utf-8',
                        help='Encoding for second subtitle file (default: utf-8)')
    
    args = parser.parse_args()
    
    # Map color names to hex values
    color_map = {
        'white': WHITE,
        'yellow': YELLOW,
        'red': RED,
        'blue': BLUE,
        'green': GREEN
    }
    
    # Get color hex values
    sub1_color = color_map.get(args.sub1_color.lower(), args.sub1_color)
    sub2_color = color_map.get(args.sub2_color.lower(), args.sub2_color)
    
    # Create merger
    merger = Merger(
        output_path=args.output_dir,
        output_name=args.output,
        output_encoding=args.encoding
    )
    
    # Add first subtitle
    print(f"Adding first subtitle: {args.sub1}")
    merger.add(
        subtitle_address=args.sub1,
        codec=args.sub1_codec,
        color=sub1_color,
        size=args.sub1_size,
        top=args.sub1_top,
        bold=args.sub1_bold,
        preserve_svg=True  # Always preserve SVG paths
    )
    
    # Add second subtitle if provided
    if args.sub2:
        print(f"Adding second subtitle: {args.sub2}")
        merger.add(
            subtitle_address=args.sub2,
            codec=args.sub2_codec,
            color=sub2_color,
            size=args.sub2_size,
            top=args.sub2_top,
            bold=args.sub2_bold,
            preserve_svg=True  # Always preserve SVG paths
        )
    
    # Merge subtitles
    print("Merging subtitles...")
    merger.merge()
    print(f"Merged subtitle saved to: {os.path.join(args.output_dir, args.output)}")

def create_svg_subtitle_file(output_path, svg_data):
    """
    Create a subtitle file with SVG path data.
    
    Args:
        output_path (str): Path to save the subtitle file
        svg_data (str): SVG path data to include in the subtitle
    """
    # Create a simple SRT file with the SVG path
    srt_content = """1
00:00:01,000 --> 00:00:05,000
{0}

""".format(svg_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    print(f"Created SVG subtitle file: {output_path}")

if __name__ == "__main__":
    main() 