#!/usr/bin/env python
# Clean SVG Subtitles - Removes duplicate SVG path entries and cleans up SRT files

import os
import sys
import re
from pathlib import Path
import argparse

def clean_srt_file(input_file, output_file=None, keep_text=True, keep_svg=True):
    """
    Clean an SRT file by removing duplicate SVG path entries and properly formatting the remaining entries.
    
    Args:
        input_file (str): Path to the input SRT file
        output_file (str): Path to the output SRT file (if None, will use input_file with _cleaned suffix)
        keep_text (bool): Whether to keep text entries (like "wa" and "daa!")
        keep_svg (bool): Whether to keep SVG path entries (at least one per timestamp)
    """
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.with_stem(input_path.stem + "_cleaned"))
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content)
        
        # Group blocks by timestamp
        timestamp_groups = {}
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
            
            # Add to timestamp group
            if timestamp not in timestamp_groups:
                timestamp_groups[timestamp] = {'svg': [], 'text': []}
            
            if is_svg:
                # Check if this SVG path is already in the group
                # We'll compare just the path data, not the font tags
                path_match = re.search(r'({\an\d}m\s+\d+\.\d+.+?\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+)', text)
                if path_match:
                    path_data = path_match.group(1)
                    # Check if this path is already in the group
                    if not any(path_data in svg_text for svg_text in timestamp_groups[timestamp]['svg']):
                        timestamp_groups[timestamp]['svg'].append(text)
                else:
                    timestamp_groups[timestamp]['svg'].append(text)
            else:
                timestamp_groups[timestamp]['text'].append(text)
        
        # Create cleaned output
        output_blocks = []
        index = 1
        
        for timestamp, entries in timestamp_groups.items():
            # Add one SVG path entry if keep_svg is True
            if keep_svg and entries['svg']:
                output_blocks.append(f"{index}\n{timestamp}\n{entries['svg'][0]}")
                index += 1
            
            # Add text entries if keep_text is True
            if keep_text:
                for text in entries['text']:
                    output_blocks.append(f"{index}\n{timestamp}\n{text}")
                    index += 1
        
        # Write output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(output_blocks))
        
        print(f"Cleaned subtitle saved to: {output_file}")
        print(f"Removed {sum(len(entries['svg']) - (1 if keep_svg and entries['svg'] else 0) for entries in timestamp_groups.values())} duplicate SVG entries")
        if not keep_text:
            print(f"Removed {sum(len(entries['text']) for entries in timestamp_groups.values())} text entries")
        
        return output_file
    
    except Exception as e:
        print(f"Error cleaning SRT file: {e}")
        return None

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Clean SRT files by removing duplicate SVG path entries')
    
    parser.add_argument('input_file', type=str, help='Input SRT file path')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: input_file with _cleaned suffix)')
    parser.add_argument('--no-text', action='store_true',
                        help='Remove all text entries (keep only SVG paths)')
    parser.add_argument('--no-svg', action='store_true',
                        help='Remove all SVG path entries (keep only text)')
    
    args = parser.parse_args()
    
    if args.no_text and args.no_svg:
        print("Error: Cannot remove both text and SVG entries. Nothing would be left.")
        return
    
    clean_srt_file(
        input_file=args.input_file,
        output_file=args.output,
        keep_text=not args.no_text,
        keep_svg=not args.no_svg
    )

if __name__ == "__main__":
    main() 