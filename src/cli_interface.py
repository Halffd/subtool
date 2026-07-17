#!/usr/bin/env python3
"""
Enhanced CLI Interface for Subtitle Merger Tool
Supports both single file merging and directory batch processing
"""
import argparse
import os
import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.merger import Merger, WHITE, YELLOW, RED, BLUE, GREEN
from src.tabs.single_files_tab import SingleFilesTab
from src.tabs.directory_tab import DirectoryTab


def detect_encoding():
    """Detect appropriate encoding based on OS."""
    if os.name == "nt":  # Windows
        return "cp1252"
    else:  # Unix-like systems
        return "utf-8"


def validate_color(color: str) -> str:
    """Validate and normalize color input."""
    color_map = {
        'white': WHITE,
        'yellow': YELLOW,
        'red': RED,
        'blue': BLUE,
        'green': GREEN,
        'default': YELLOW
    }
    
    color_lower = color.lower()
    if color_lower in color_map:
        return color_map[color_lower]
    elif color.startswith('#') and len(color) == 7:
        # Validate hex color
        if re.match(r'^#[0-9A-Fa-f]{6}$', color):
            return color
        else:
            raise ValueError(f"Invalid hex color format: {color}")
    else:
        raise ValueError(f"Invalid color: {color}. Use white, yellow, red, blue, green, or #RRGGBB format.")


def merge_single_files(
    sub1_path: str,
    sub2_path: str,
    output_path: str,
    color: str = "yellow",
    codec: str = "utf-8",
    sub1_size: int = 16,
    sub2_size: int = 16,
    sub1_delay: int = 0,
    sub2_delay: int = 0,
    sub1_bold: bool = False,
    sub2_bold: bool = False,
    enable_svg_filtering: bool = False,
    remove_text_entries: bool = False,
    preserve_svg: bool = True,
    convert_to_ass: bool = False
):
    """
    Merge two subtitle files with specified options.
    
    Args:
        sub1_path: Path to first subtitle file
        sub2_path: Path to second subtitle file
        output_path: Path for output merged file
        color: Color for first subtitle
        codec: Text encoding
        sub1_size: Font size for first subtitle
        sub2_size: Font size for second subtitle
        sub1_delay: Time delay for first subtitle (ms)
        sub2_delay: Time delay for second subtitle (ms)
        sub1_bold: Whether first subtitle is bold
        sub2_bold: Whether second subtitle is bold
        enable_svg_filtering: Whether to enable SVG filtering
        remove_text_entries: Whether to remove text entries
        preserve_svg: Whether to preserve SVG paths
        convert_to_ass: Whether to convert to ASS format
    """
    try:
        # Normalize color
        normalized_color = validate_color(color)
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create merger instance
        merger = Merger(
            output_path=str(output_dir),
            output_name=Path(output_path).name,
            output_encoding=codec
        )
        
        # Apply SVG filtering options
        merger.enable_svg_filtering(enable_svg_filtering)
        merger.set_remove_text_entries(remove_text_entries)
        
        # Add first subtitle
        merger.add(
            sub1_path,
            codec=codec,
            color=normalized_color,
            size=sub1_size,
            time_offset=sub1_delay,
            bold=sub1_bold,
            preserve_svg=preserve_svg
        )
        
        # Add second subtitle
        merger.add(
            sub2_path,
            codec=codec,
            color=WHITE,  # Second subtitle is always white
            size=sub2_size,
            time_offset=sub2_delay,
            bold=sub2_bold,
            preserve_svg=preserve_svg
        )
        
        # Perform merge
        merger.merge()
        print(f"Successfully merged subtitles to: {output_path}")
        
        # Convert to ASS if requested
        if convert_to_ass:
            from src.utils.ass_converter import create_ass_from_srt
            ass_path = str(Path(output_path).with_suffix('.ass'))
            
            style_kwargs = {
                'font': "MS Gothic",  # Japanese font
                'font_size': sub1_size,
                'ruby_font_size': sub1_size // 2,  # Half the size for ruby
                'text_color': normalized_color,
                'outline_size': 1.5,  # Thinner outline
                'shadow_size': 0.5,  # Subtle shadow
                'auto_generate_furigana': True,  # Use automatic furigana generation
                'advanced_styling': True  # Use advanced styling with separate dialogue entries
            }
            
            ass_file = create_ass_from_srt(
                srt_file_path=output_path,
                output_dir=str(output_dir),
                **style_kwargs
            )
            
            print(f"Converted to ASS format: {ass_file}")
        
        return True
        
    except Exception as e:
        print(f"Error during merge operation: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_merge_directory(
    input_dir: str,
    video_dir: str,
    output_dir: Optional[str] = None,
    sub1_pattern: str = r'.*\.srt$',
    sub2_pattern: str = r'.*\.srt$',
    sub1_episode_pattern: str = r'\d+',
    sub2_episode_pattern: str = r'\d+',
    sub1_delay: int = 0,
    sub2_delay: int = 0,
    codec: str = "utf-8",
    enable_alass_sync: bool = False,
    alass_path: str = "",
    alass_interval: int = 100,
    alass_split_penalty: float = 10.0,
    alass_sub_fps: float = 23.976,
    alass_ref_fps: float = 23.976,
    disable_fps_guessing: bool = False,
    enable_svg_filtering: bool = False,
    remove_text_entries: bool = False,
    preserve_svg: bool = True,
    convert_to_ass: bool = False,
    sub1_size: int = 16,
    sub2_size: int = 16,
    sub1_bold: bool = False,
    sub2_bold: bool = False,
    color: str = "yellow"
):
    """
    Batch merge subtitle files in a directory based on patterns.
    
    Args:
        input_dir: Directory containing subtitle files
        video_dir: Directory containing video files for ALASS sync
        output_dir: Directory for output files (defaults to input_dir)
        sub1_pattern: Regex pattern for first subtitle type
        sub2_pattern: Regex pattern for second subtitle type
        sub1_episode_pattern: Regex pattern for episode numbers in sub1
        sub2_episode_pattern: Regex pattern for episode numbers in sub2
        sub1_delay: Time delay for first subtitle (ms)
        sub2_delay: Time delay for second subtitle (ms)
        codec: Text encoding
        enable_alass_sync: Whether to enable ALASS auto-sync
        alass_path: Path to ALASS executable
        alass_interval: ALASS interval parameter (ms)
        alass_split_penalty: ALASS split penalty parameter
        alass_sub_fps: ALASS subtitle FPS
        alass_ref_fps: ALASS reference FPS
        disable_fps_guessing: Disable FPS guessing in ALASS
        enable_svg_filtering: Whether to enable SVG filtering
        remove_text_entries: Whether to remove text entries
        preserve_svg: Whether to preserve SVG paths
        convert_to_ass: Whether to convert to ASS format
        sub1_size: Font size for first subtitle
        sub2_size: Font size for second subtitle
        sub1_bold: Whether first subtitle is bold
        sub2_bold: Whether second subtitle is bold
        color: Color for first subtitle
    """
    try:
        import re
        import subprocess
        from pathlib import Path
        from src.utils.merger import Merger, WHITE, YELLOW
        
        input_path = Path(input_dir)
        video_path = Path(video_dir)
        output_path = Path(output_dir) if output_dir else input_path
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find subtitle files
        all_srt_files = list(input_path.glob('*.srt'))
        print(f"Found {len(all_srt_files)} total .srt files")
        
        # Find matching files using patterns
        sub1_files = [f for f in all_srt_files
                     if re.search(sub1_pattern, f.name, re.IGNORECASE)]
        sub2_files = [f for f in all_srt_files
                     if re.search(sub2_pattern, f.name, re.IGNORECASE)]
        
        print(f"Found {len(sub1_files)} sub1 files and {len(sub2_files)} sub2 files")
        
        # Create episode pairs dictionary
        episode_subs = {}
        
        # Process sub1 files
        for sub1 in sub1_files:
            try:
                # Try SxxExx pattern first
                sxxexx_match = re.search(r'[Ss](\d+)[Ee](\d+)', sub1.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                else:
                    # Try configured pattern
                    match = re.search(sub1_episode_pattern, sub1.stem)
                    if match:
                        ep_num = match.group(1)
                        season_num = '01'  # Default season
                    else:
                        # Try extracting episode number from filename
                        ep_match = re.search(r'(?:^|\s|_|-|\[)(\d{1,2})(?:\s|$|\]|\[|\()', sub1.stem)
                        if ep_match:
                            ep_num = ep_match.group(1)
                            season_num = '01'  # Default season
                        else:
                            print(f"Could not extract episode info from sub1 file: {sub1.name}")
                            continue
                
                # Create a unique key combining season and episode
                ep_key = f"S{season_num}E{ep_num}"
                
                if ep_key not in episode_subs:
                    episode_subs[ep_key] = {
                        'sub1': sub1,
                        'season': season_num,
                        'episode': ep_num,
                        'file_name': sub1.name
                    }
                    print(f"Found sub1 for {ep_key}: {sub1.name}")
                    
            except Exception as e:
                print(f"Error processing sub1 file {sub1}: {e}")
        
        # Process sub2 files
        for sub2 in sub2_files:
            try:
                # Try SxxExx pattern first
                sxxexx_match = re.search(r'[Ss](\d+)[Ee](\d+)', sub2.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                else:
                    # Try configured pattern
                    match = re.search(sub2_episode_pattern, sub2.stem)
                    if match:
                        ep_num = match.group(1)
                        season_num = '01'  # Default season
                    else:
                        # Try extracting episode number from filename
                        ep_match = re.search(r'(?:^|\s|_|-|\[)(\d{1,2})(?:\s|$|\]|\[|\()', sub2.stem)
                        if ep_match:
                            ep_num = ep_match.group(1)
                            season_num = '01'  # Default season
                        else:
                            print(f"Could not extract episode info from sub2 file: {sub2.name}")
                            continue
                
                # Create a unique key combining season and episode
                ep_key = f"S{season_num}E{ep_num}"
                
                if ep_key in episode_subs:
                    episode_subs[ep_key]['sub2'] = sub2
                    print(f"Found sub2 for {ep_key}: {sub2.name}")
                else:
                    print(f"Found unmatched sub2 for {ep_key}: {sub2.name}")
                    
            except Exception as e:
                print(f"Error processing sub2 file {sub2}: {e}")
        
        # Display summary of matched subtitles
        matched_pairs = [k for k, v in episode_subs.items() if 'sub1' in v and 'sub2' in v]
        print(f"Found {len(matched_pairs)} matched subtitle pairs")
        
        # Process matched pairs
        success_count = 0
        for pair in matched_pairs:
            sub1_file = episode_subs[pair]['sub1']
            sub2_file = episode_subs[pair]['sub2']
            
            # Find corresponding video file if ALASS sync is enabled
            video_file = None
            if enable_alass_sync:
                # Look for video files with similar names
                video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
                for ext in video_extensions:
                    potential_video = video_path / f"{sub1_file.stem}{ext}"
                    if potential_video.exists():
                        video_file = potential_video
                        break
                    
                    # Also try with episode number patterns
                    # Try to find video file with same episode number
                    for video_file_in_dir in video_path.glob('*'):
                        if video_file_in_dir.suffix.lower() in video_extensions:
                            # Check if episode number matches
                            if re.search(sub1_episode_pattern, video_file_in_dir.stem):
                                video_match = re.search(sub1_episode_pattern, video_file_in_dir.stem)
                                if video_match and video_match.group(1) == episode_subs[pair]['episode']:
                                    video_file = video_file_in_dir
                                    break
                            
                            # Check SxxExx pattern
                            sxxexx_match = re.search(r'[Ss](\d+)[Ee](\d+)', video_file_in_dir.stem)
                            if sxxexx_match:
                                ep_num = sxxexx_match.group(2)
                                if ep_num == episode_subs[pair]['episode']:
                                    video_file = video_file_in_dir
                                    break
                
                if not video_file:
                    print(f"Warning: No matching video file found for {sub1_file.name}, skipping ALASS sync for this pair")
            
            # Generate output filename
            output_name = f"{sub1_file.stem}_merged.srt"
            output_file = output_path / output_name
            
            print(f"Merging {sub1_file.name} and {sub2_file.name} -> {output_file.name}")
            
            # Prepare for ALASS sync if enabled
            temp_sub1_path = str(sub1_file)
            temp_sub2_path = str(sub2_file)
            
            if enable_alass_sync and video_file:
                try:
                    # Sync first subtitle with ALASS
                    temp_sub1_path = sync_subtitle_with_alass(
                        str(video_file), str(sub1_file), alass_path, alass_interval, 
                        alass_split_penalty, alass_sub_fps, alass_ref_fps, disable_fps_guessing
                    )
                    
                    # Sync second subtitle with ALASS
                    temp_sub2_path = sync_subtitle_with_alass(
                        str(video_file), str(sub2_file), alass_path, alass_interval, 
                        alass_split_penalty, alass_sub_fps, alass_ref_fps, disable_fps_guessing
                    )
                    
                    print(f"  ALASS sync completed for both subtitles")
                except Exception as e:
                    print(f"  Warning: ALASS sync failed, using original files: {e}")
            
            # Create merger instance
            merger = Merger(
                output_path=str(output_path),
                output_name=output_file.name,
                output_encoding=codec
            )
            
            # Apply SVG filtering options
            merger.enable_svg_filtering(enable_svg_filtering)
            merger.set_remove_text_entries(remove_text_entries)
            
            # Normalize color
            normalized_color = validate_color(color)
            
            # Add first subtitle
            merger.add(
                temp_sub1_path,
                codec=codec,
                color=normalized_color,
                size=sub1_size,
                time_offset=sub1_delay,
                bold=sub1_bold,
                preserve_svg=preserve_svg
            )
            
            # Add second subtitle
            merger.add(
                temp_sub2_path,
                codec=codec,
                color=WHITE,  # Second subtitle is always white
                size=sub2_size,
                time_offset=sub2_delay,
                bold=sub2_bold,
                preserve_svg=preserve_svg
            )
            
            # Perform merge
            merger.merge()
            print(f"  Merged: {output_file.name}")
            success_count += 1
            
            # Convert to ASS if requested
            if convert_to_ass:
                from src.utils.ass_converter import create_ass_from_srt
                ass_path = str(output_file.with_suffix('.ass'))
                
                style_kwargs = {
                    'font': "MS Gothic",  # Japanese font
                    'font_size': sub1_size,
                    'ruby_font_size': sub1_size // 2,  # Half the size for ruby
                    'text_color': normalized_color,
                    'outline_size': 1.5,  # Thinner outline
                    'shadow_size': 0.5,  # Subtle shadow
                    'auto_generate_furigana': True,  # Use automatic furigana generation
                    'advanced_styling': True  # Use advanced styling with separate dialogue entries
                }
                
                ass_file = create_ass_from_srt(
                    srt_file_path=str(output_file),
                    output_dir=str(output_path),
                    **style_kwargs
                )
                
                print(f"  Converted to ASS: {Path(ass_file).name}")
        
        print(f"\nBatch processing completed. Successfully processed {success_count} pairs.")
        return True
        
    except Exception as e:
        print(f"Error during batch merge operation: {e}")
        import traceback
        traceback.print_exc()
        return False


def sync_subtitle_with_alass(video_path: str, subtitle_path: str, alass_path: str = "", 
                           alass_interval: int = 100, alass_split_penalty: float = 10.0,
                           alass_sub_fps: float = 23.976, alass_ref_fps: float = 23.976,
                           disable_fps_guessing: bool = False) -> str:
    """Synchronize subtitle with ALASS using the video as reference."""
    import subprocess
    import os
    from pathlib import Path
    
    # Determine ALASS path
    if not alass_path:
        # Try to find alass in system PATH
        import shutil
        alass_path = shutil.which('alass')
        if not alass_path:
            # Default fallback path
            alass_path = '/usr/bin/alass'
    
    try:
        if not os.path.exists(alass_path):
            print(f"ALASS not found at {alass_path}")
            return subtitle_path

        # Create temporary file for synced subtitle
        temp_dir = Path(subtitle_path).parent
        synced_path = temp_dir / f"synced_{Path(subtitle_path).name}"

        # Build ALASS command with parameters
        cmd = [
            alass_path,
            "--interval", str(alass_interval),
            "--split-penalty", str(alass_split_penalty),
            "--sub-fps-inc", str(alass_sub_fps),
            "--sub-fps-ref", str(alass_ref_fps)
        ]

        # Add disable-fps-guessing if checked
        if disable_fps_guessing:
            cmd.append("--disable-fps-guessing")

        # Add input/output files
        cmd.extend([video_path, subtitle_path, str(synced_path)])

        print(f"Running ALASS command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            print(f"ALASS sync failed: {process.stderr}")
            return subtitle_path

        print(f"ALASS sync successful, output saved to {synced_path}")
        return str(synced_path)

    except Exception as e:
        print(f"Error during ALASS sync: {e}")
        return subtitle_path


def main():
    parser = argparse.ArgumentParser(
        description="Subtitle Merger Tool - CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge two subtitle files
  python cli_interface.py single file1.srt file2.srt output.srt --color yellow --codec utf-8
  
  # Batch merge files in a directory
  python cli_interface.py batch /path/to/subtitles /path/to/videos --sub1-pattern ".*jpn.*\\.srt$" --sub2-pattern ".*eng.*\\.srt$"
  
  # Merge with custom font sizes and delays
  python cli_interface.py single file1.srt file2.srt output.srt --sub1-size 20 --sub2-size 18 --sub1-delay 100
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode', required=True)
    
    # Single file merge parser
    single_parser = subparsers.add_parser('single', help='Merge two individual subtitle files')
    single_parser.add_argument('sub1', help='Path to first subtitle file')
    single_parser.add_argument('sub2', help='Path to second subtitle file')
    single_parser.add_argument('output', help='Path for output merged file')
    single_parser.add_argument('--color', default='yellow', help='Color for first subtitle (white, yellow, red, blue, green, or #RRGGBB)')
    single_parser.add_argument('--codec', default='utf-8', help='Text encoding (default: utf-8)')
    single_parser.add_argument('--sub1-size', type=int, default=16, help='Font size for first subtitle (default: 16)')
    single_parser.add_argument('--sub2-size', type=int, default=16, help='Font size for second subtitle (default: 16)')
    single_parser.add_argument('--sub1-delay', type=int, default=0, help='Time delay for first subtitle in ms (default: 0)')
    single_parser.add_argument('--sub2-delay', type=int, default=0, help='Time delay for second subtitle in ms (default: 0)')
    single_parser.add_argument('--sub1-bold', action='store_true', help='Make first subtitle bold')
    single_parser.add_argument('--sub2-bold', action='store_true', help='Make second subtitle bold')
    single_parser.add_argument('--enable-svg-filtering', action='store_true', help='Enable SVG filtering')
    single_parser.add_argument('--remove-text-entries', action='store_true', help='Remove text entries')
    single_parser.add_argument('--preserve-svg', action='store_true', default=True, help='Preserve SVG paths (default: True)')
    single_parser.add_argument('--no-preserve-svg', action='store_false', dest='preserve_svg', help='Do not preserve SVG paths')
    single_parser.add_argument('--convert-to-ass', action='store_true', help='Convert output to ASS format with furigana')
    
    # Directory batch processing parser
    batch_parser = subparsers.add_parser('batch', help='Batch merge subtitle files in a directory')
    batch_parser.add_argument('input_dir', help='Directory containing subtitle files')
    batch_parser.add_argument('video_dir', help='Directory containing video files for ALASS sync')
    batch_parser.add_argument('--output-dir', help='Directory for output files (defaults to input directory)')
    batch_parser.add_argument('--sub1-pattern', default=r'.*\.srt$', help='Regex pattern for first subtitle type (default: .*\\.srt$)')
    batch_parser.add_argument('--sub2-pattern', default=r'.*\.srt$', help='Regex pattern for second subtitle type (default: .*\\.srt$)')
    batch_parser.add_argument('--sub1-episode-pattern', default=r'\d+', help='Regex pattern for episode numbers in sub1 (default: \\d+)')
    batch_parser.add_argument('--sub2-episode-pattern', default=r'\d+', help='Regex pattern for episode numbers in sub2 (default: \\d+)')
    batch_parser.add_argument('--sub1-delay', type=int, default=0, help='Time delay for first subtitle in ms (default: 0)')
    batch_parser.add_argument('--sub2-delay', type=int, default=0, help='Time delay for second subtitle in ms (default: 0)')
    batch_parser.add_argument('--codec', default='utf-8', help='Text encoding (default: utf-8)')
    batch_parser.add_argument('--enable-alass-sync', action='store_true', help='Enable ALASS auto-sync')
    batch_parser.add_argument('--alass-path', default='', help='Path to ALASS executable')
    batch_parser.add_argument('--alass-interval', type=int, default=100, help='ALASS interval parameter in ms (default: 100)')
    batch_parser.add_argument('--alass-split-penalty', type=float, default=10.0, help='ALASS split penalty parameter (default: 10.0)')
    batch_parser.add_argument('--alass-sub-fps', type=float, default=23.976, help='ALASS subtitle FPS (default: 23.976)')
    batch_parser.add_argument('--alass-ref-fps', type=float, default=23.976, help='ALASS reference FPS (default: 23.976)')
    batch_parser.add_argument('--disable-fps-guessing', action='store_true', help='Disable FPS guessing in ALASS')
    batch_parser.add_argument('--enable-svg-filtering', action='store_true', help='Enable SVG filtering')
    batch_parser.add_argument('--remove-text-entries', action='store_true', help='Remove text entries')
    batch_parser.add_argument('--preserve-svg', action='store_true', default=True, help='Preserve SVG paths (default: True)')
    batch_parser.add_argument('--no-preserve-svg', action='store_false', dest='preserve_svg', help='Do not preserve SVG paths')
    batch_parser.add_argument('--convert-to-ass', action='store_true', help='Convert output to ASS format with furigana')
    batch_parser.add_argument('--sub1-size', type=int, default=16, help='Font size for first subtitle (default: 16)')
    batch_parser.add_argument('--sub2-size', type=int, default=16, help='Font size for second subtitle (default: 16)')
    batch_parser.add_argument('--sub1-bold', action='store_true', help='Make first subtitle bold')
    batch_parser.add_argument('--sub2-bold', action='store_true', help='Make second subtitle bold')
    batch_parser.add_argument('--color', default='yellow', help='Color for first subtitle (white, yellow, red, blue, green, or #RRGGBB)')
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        success = merge_single_files(
            sub1_path=args.sub1,
            sub2_path=args.sub2,
            output_path=args.output,
            color=args.color,
            codec=args.codec,
            sub1_size=args.sub1_size,
            sub2_size=args.sub2_size,
            sub1_delay=args.sub1_delay,
            sub2_delay=args.sub2_delay,
            sub1_bold=args.sub1_bold,
            sub2_bold=args.sub2_bold,
            enable_svg_filtering=args.enable_svg_filtering,
            remove_text_entries=args.remove_text_entries,
            preserve_svg=args.preserve_svg,
            convert_to_ass=args.convert_to_ass
        )
        sys.exit(0 if success else 1)
    
    elif args.mode == 'batch':
        success = batch_merge_directory(
            input_dir=args.input_dir,
            video_dir=args.video_dir,
            output_dir=args.output_dir,
            sub1_pattern=args.sub1_pattern,
            sub2_pattern=args.sub2_pattern,
            sub1_episode_pattern=args.sub1_episode_pattern,
            sub2_episode_pattern=args.sub2_episode_pattern,
            sub1_delay=args.sub1_delay,
            sub2_delay=args.sub2_delay,
            codec=args.codec,
            enable_alass_sync=args.enable_alass_sync,
            alass_path=args.alass_path,
            alass_interval=args.alass_interval,
            alass_split_penalty=args.alass_split_penalty,
            alass_sub_fps=args.alass_sub_fps,
            alass_ref_fps=args.alass_ref_fps,
            disable_fps_guessing=args.disable_fps_guessing,
            enable_svg_filtering=args.enable_svg_filtering,
            remove_text_entries=args.remove_text_entries,
            preserve_svg=args.preserve_svg,
            convert_to_ass=args.convert_to_ass,
            sub1_size=args.sub1_size,
            sub2_size=args.sub2_size,
            sub1_bold=args.sub1_bold,
            sub2_bold=args.sub2_bold,
            color=args.color
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()