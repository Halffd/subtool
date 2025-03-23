#!/usr/bin/env python
# Fix SVG Stars - Cleans up subtitle files with duplicate SVG star patterns

import os
import sys
import re
from pathlib import Path

def fix_svg_stars(input_file, output_file=None, remove_text=False):
    """
    Fix a subtitle file by removing duplicate SVG star patterns.
    
    Args:
        input_file (str): Path to the input subtitle file
        output_file (str): Path to the output subtitle file (default: input_file with _fixed suffix)
        remove_text (bool): Whether to remove text entries like "wa" and "daa!"
    """
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.with_stem(input_path.stem + "_fixed"))
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content)
        
        # Process blocks
        processed_blocks = []
        seen_timestamps = set()
        seen_svg_timestamps = set()
        
        for block in blocks:
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # Extract timestamp and text
            index = lines[0].strip()
            timestamp = lines[1].strip()
            text = '\n'.join(lines[2:])
            
            # Skip entries with just "--"
            if text.strip() == '--':
                continue
            
            # Check if this is an SVG path entry
            is_svg = bool(re.search(r'{\an\d}m\s+\d+\.\d+\s+\d+\.\d+\s+b', text))
            
            # Skip duplicate SVG entries for the same timestamp
            if is_svg:
                if timestamp in seen_svg_timestamps:
                    continue
                seen_svg_timestamps.add(timestamp)
            elif remove_text:
                # Skip text entries if remove_text is True
                continue
            
            # Add to processed blocks
            processed_blocks.append(block)
        
        # Renumber blocks
        final_blocks = []
        for i, block in enumerate(processed_blocks, 1):
            lines = block.strip().split('\n')
            lines[0] = str(i)  # Replace index
            final_blocks.append('\n'.join(lines))
        
        # Write output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(final_blocks))
        
        print(f"Fixed subtitle saved to: {output_file}")
        print(f"Original blocks: {len(blocks)}")
        print(f"Processed blocks: {len(final_blocks)}")
        
        return output_file
    
    except Exception as e:
        print(f"Error fixing subtitle file: {e}")
        return None

def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix subtitle files with duplicate SVG star patterns')
    
    parser.add_argument('input_file', type=str, help='Input subtitle file path')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: input_file with _fixed suffix)')
    parser.add_argument('--remove-text', '-r', action='store_true',
                        help='Remove text entries like "wa" and "daa!"')
    
    args = parser.parse_args()
    
    fix_svg_stars(
        input_file=args.input_file,
        output_file=args.output,
        remove_text=args.remove_text
    )

if __name__ == "__main__":
    # If no arguments are provided, show help
    if len(sys.argv) == 1:
        print("Usage: python fix_svg_stars.py input_file [--output output_file] [--remove-text]")
        print("\nThis script cleans up subtitle files with duplicate SVG star patterns.")
        print("It removes duplicate SVG entries and optionally removes text entries like 'wa' and 'daa!'.")
        print("\nExample:")
        print("  python fix_svg_stars.py subtitles.srt")
        print("  python fix_svg_stars.py subtitles.srt --output cleaned.srt --remove-text")
        sys.exit(0)
    
    main() 