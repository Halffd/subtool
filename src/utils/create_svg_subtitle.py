#!/usr/bin/env python
# Create SVG Subtitle - A tool to create subtitle files with SVG path data

import os
import sys
import argparse
from pathlib import Path

def main():
    """Main function to handle command line arguments and create SVG subtitle file."""
    parser = argparse.ArgumentParser(description='Create subtitle file with SVG path data')
    
    parser.add_argument('--output', '-o', type=str, default='svg_subtitle.srt',
                        help='Output file name (default: svg_subtitle.srt)')
    parser.add_argument('--output-dir', '-d', type=str, default='.',
                        help='Output directory (default: current directory)')
    parser.add_argument('--start-time', '-s', type=str, default='00:00:01,000',
                        help='Start time (default: 00:00:01,000)')
    parser.add_argument('--end-time', '-e', type=str, default='00:00:05,000',
                        help='End time (default: 00:00:05,000)')
    parser.add_argument('--position', '-p', type=int, default=9,
                        help='Position (1-9, default: 9 for top-right)')
    parser.add_argument('--font-face', '-f', type=str, default='Brady Bunch Remastered',
                        help='Font face (default: Brady Bunch Remastered)')
    parser.add_argument('--font-size', '-z', type=int, default=48,
                        help='Font size (default: 48)')
    parser.add_argument('--color', '-c', type=str, default='#FFFFFF',
                        help='Font color (default: #FFFFFF)')
    parser.add_argument('--svg-path', type=str, required=False,
                        help='SVG path data (if not provided, will read from stdin)')
    
    args = parser.parse_args()
    
    # Get SVG path data
    svg_path = args.svg_path
    if not svg_path:
        print("Enter SVG path data (press Ctrl+D when done):")
        svg_path = sys.stdin.read().strip()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output path
    output_path = output_dir / args.output
    
    # Create subtitle content
    subtitle_content = create_svg_subtitle(
        svg_path=svg_path,
        start_time=args.start_time,
        end_time=args.end_time,
        position=args.position,
        font_face=args.font_face,
        font_size=args.font_size,
        color=args.color
    )
    
    # Write subtitle file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(subtitle_content)
    
    print(f"Created SVG subtitle file: {output_path}")

def create_svg_subtitle(svg_path, start_time='00:00:01,000', end_time='00:00:05,000', 
                       position=9, font_face='Brady Bunch Remastered', font_size=48, color='#FFFFFF'):
    """
    Create a subtitle file with SVG path data.
    
    Args:
        svg_path (str): SVG path data
        start_time (str): Start time in format HH:MM:SS,mmm
        end_time (str): End time in format HH:MM:SS,mmm
        position (int): Position (1-9)
        font_face (str): Font face
        font_size (int): Font size
        color (str): Font color in hex format
        
    Returns:
        str: Subtitle content
    """
    # Format the SVG path with font and position tags
    formatted_svg = f'<font face="{font_face}" size="{font_size}" color="{color}">{{\\an{position}}}{svg_path}</font>'
    
    # Create subtitle content
    subtitle_content = f"""1
{start_time} --> {end_time}
{formatted_svg}

"""
    
    return subtitle_content

if __name__ == "__main__":
    main() 