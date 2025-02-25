#!/usr/bin/env python3
"""
SRT to Furigana ASS Converter

This script converts SRT subtitle files to ASS format with furigana (ruby text)
for Japanese text. It processes all SRT files in the specified directory.

Usage:
    python srt_to_furigana_ass.py [input_directory] [output_directory]

If no directories are specified, it uses the current directory for both input and output.
"""

import os
import sys
import re
import argparse
import pysubs2
from pathlib import Path

# Default style settings
DEFAULT_FONT = "Arial"
DEFAULT_FONT_SIZE = 48
DEFAULT_RUBY_FONT_SIZE = 24
DEFAULT_TEXT_COLOR = "&H00FFFFFF"  # White in ASS format (AABBGGRR)
DEFAULT_RUBY_COLOR = "&H00FFFFFF"  # White in ASS format
DEFAULT_OUTLINE_COLOR = "&H00000000"  # Black in ASS format
DEFAULT_SHADOW_COLOR = "&H00000000"  # Black in ASS format
DEFAULT_OUTLINE_SIZE = 2
DEFAULT_RUBY_OUTLINE_SIZE = 1
DEFAULT_SHADOW_SIZE = 2
DEFAULT_RUBY_SHADOW_SIZE = 1

def create_ass_from_srt(srt_file, output_dir=None, config=None):
    """
    Convert an SRT file to ASS format with furigana using pysubs2.
    
    Args:
        srt_file (str): Path to the SRT file
        output_dir (str, optional): Directory to save the output ASS file
        config (dict, optional): Configuration options for styling
    
    Returns:
        str: Path to the output ASS file
    """
    try:
        # Use default config if none provided
        if config is None:
            config = {
                'font': DEFAULT_FONT,
                'font_size': DEFAULT_FONT_SIZE,
                'ruby_font_size': DEFAULT_RUBY_FONT_SIZE,
                'text_color': DEFAULT_TEXT_COLOR,
                'ruby_color': DEFAULT_RUBY_COLOR,
                'outline_color': DEFAULT_OUTLINE_COLOR,
                'shadow_color': DEFAULT_SHADOW_COLOR,
                'outline_size': DEFAULT_OUTLINE_SIZE,
                'ruby_outline_size': DEFAULT_RUBY_OUTLINE_SIZE,
                'shadow_size': DEFAULT_SHADOW_SIZE,
                'ruby_shadow_size': DEFAULT_RUBY_SHADOW_SIZE
            }
        
        # Parse the SRT file using pysubs2
        subs = pysubs2.load(srt_file, encoding="utf-8")
        
        # Create output file path
        srt_path = Path(srt_file)
        if output_dir:
            output_path = Path(output_dir) / f"{srt_path.stem}.ass"
        else:
            output_path = srt_path.with_suffix('.ass')
        
        # Create styles for the ASS file
        subs.styles = {}  # Clear existing styles
        
        # Add Default style
        default_style = pysubs2.SSAStyle(
            fontname=config['font'],
            fontsize=config['font_size'],
            primarycolor=config['text_color'],
            secondarycolor="&H000000FF",
            outlinecolor=config['outline_color'],
            backcolor=config['shadow_color'],
            bold=False,
            italic=False,
            underline=False,
            strikeout=False,
            scalex=100,
            scaley=100,
            spacing=0,
            angle=0,
            borderstyle=1,
            outline=config['outline_size'],
            shadow=config['shadow_size'],
            alignment=2,
            marginl=10,
            marginr=10,
            marginv=20,
            encoding=1
        )
        subs.styles["Default"] = default_style
        
        # Add Ruby style
        ruby_style = pysubs2.SSAStyle(
            fontname=config['font'],
            fontsize=config['ruby_font_size'],
            primarycolor=config['ruby_color'],
            secondarycolor="&H000000FF",
            outlinecolor=config['outline_color'],
            backcolor=config['shadow_color'],
            bold=False,
            italic=False,
            underline=False,
            strikeout=False,
            scalex=100,
            scaley=100,
            spacing=0,
            angle=0,
            borderstyle=1,
            outline=config['ruby_outline_size'],
            shadow=config['ruby_shadow_size'],
            alignment=8,
            marginl=10,
            marginr=10,
            marginv=20,
            encoding=1
        )
        subs.styles["Ruby"] = ruby_style
        
        # Process each subtitle line
        for line in subs:
            # Add ruby tags to the text
            line.text = add_ruby_tags(line.text)
        
        # Save the ASS file
        subs.save(output_path)
        
        print(f"Converted {srt_file} to {output_path}")
        return str(output_path)
    
    except Exception as e:
        print(f"Error converting {srt_file}: {e}")
        return None

def add_ruby_tags(text):
    """
    Add ASS ruby tags to text with furigana in parentheses.
    
    This function uses a regular expression to find patterns like:
    - 漢字(かんじ)
    - 日本語(にほんご)
    
    And converts them to ASS ruby format using the proper tag:
    - {\\rt(かんじ)}漢字
    - {\\rt(にほんご)}日本語
    
    Args:
        text (str): The text to process
    
    Returns:
        str: Text with ASS ruby tags
    """
    # Replace newlines with ASS newline format
    text = text.replace('\n', '\\N')
    
    # Define the pattern for finding kanji with furigana in parentheses
    # This pattern looks for any non-whitespace characters followed by text in parentheses
    pattern = r'(\S+?)\(([^)]+)\)'
    
    # Function to replace matches with ASS ruby tags
    def replace_with_ruby(match):
        kanji = match.group(1)
        furigana = match.group(2)
        
        # Use the standard \rt tag for ruby text
        return f"{{\\rt({furigana})}}{kanji}"
    
    # Apply the replacement
    result = re.sub(pattern, replace_with_ruby, text)
    
    return result

def process_directory(input_dir='.', output_dir=None, config=None):
    """
    Process all SRT files in the input directory.
    
    Args:
        input_dir (str): Directory containing SRT files
        output_dir (str, optional): Directory to save the output ASS files
        config (dict, optional): Configuration options for styling
    """
    input_path = Path(input_dir)
    
    # Create output directory if it doesn't exist
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    else:
        output_path = input_path
    
    # Find all SRT files
    srt_files = list(input_path.glob('*.srt'))
    
    if not srt_files:
        print(f"No SRT files found in {input_dir}")
        return
    
    print(f"Found {len(srt_files)} SRT files in {input_dir}")
    
    # Process each SRT file
    for srt_file in srt_files:
        create_ass_from_srt(str(srt_file), str(output_path), config)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert SRT files to ASS with furigana support')
    parser.add_argument('input_dir', nargs='?', default='.', help='Input directory containing SRT files')
    parser.add_argument('output_dir', nargs='?', help='Output directory for ASS files')
    
    # Style options
    parser.add_argument('--font', default=DEFAULT_FONT, help='Font to use for subtitles')
    parser.add_argument('--font-size', type=int, default=DEFAULT_FONT_SIZE, help='Font size for main text')
    parser.add_argument('--ruby-font-size', type=int, default=DEFAULT_RUBY_FONT_SIZE, help='Font size for ruby text')
    parser.add_argument('--text-color', default=DEFAULT_TEXT_COLOR, help='Color for main text in ASS format (&HAABBGGRR)')
    parser.add_argument('--ruby-color', default=DEFAULT_RUBY_COLOR, help='Color for ruby text in ASS format (&HAABBGGRR)')
    parser.add_argument('--outline-color', default=DEFAULT_OUTLINE_COLOR, help='Color for text outline in ASS format (&HAABBGGRR)')
    parser.add_argument('--shadow-color', default=DEFAULT_SHADOW_COLOR, help='Color for text shadow in ASS format (&HAABBGGRR)')
    parser.add_argument('--outline-size', type=int, default=DEFAULT_OUTLINE_SIZE, help='Size of text outline')
    parser.add_argument('--shadow-size', type=int, default=DEFAULT_SHADOW_SIZE, help='Size of text shadow')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Create configuration from arguments
    config = {
        'font': args.font,
        'font_size': args.font_size,
        'ruby_font_size': args.ruby_font_size,
        'text_color': args.text_color,
        'ruby_color': args.ruby_color,
        'outline_color': args.outline_color,
        'shadow_color': args.shadow_color,
        'outline_size': args.outline_size,
        'ruby_outline_size': DEFAULT_RUBY_OUTLINE_SIZE,
        'shadow_size': args.shadow_size,
        'ruby_shadow_size': DEFAULT_RUBY_SHADOW_SIZE
    }
    
    process_directory(args.input_dir, args.output_dir, config) 