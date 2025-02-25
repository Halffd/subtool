#!/usr/bin/env python3
"""
ASS Converter Utility

This module provides functionality to convert SRT subtitle files to ASS format
with proper ruby text (furigana) support for Japanese text, matching the format
used in professional anime subtitles with precise positioning and styling.
"""

import os
import re
from pathlib import Path
import pysubs2
from .furigana_generator import FuriganaGenerator

# Default style settings
DEFAULT_FONT = "MS Gothic"
DEFAULT_FONT_SIZE = 48
DEFAULT_RUBY_FONT_SIZE = 24
DEFAULT_TEXT_COLOR = "&H00FFFFFF"  # White in ASS format
DEFAULT_RUBY_COLOR = "&H00FFFFFF"  # White in ASS format
DEFAULT_OUTLINE_COLOR = "&H00000000"  # Black in ASS format
DEFAULT_SHADOW_COLOR = "&H00000000"  # Black in ASS format
DEFAULT_OUTLINE_SIZE = 2
DEFAULT_SHADOW_SIZE = 2

# Base position for subtitles (center of screen)
BASE_X = 960  # Center of 1920 width
BASE_Y_BOTTOM = 1011  # Bottom line position from example.ass
BASE_Y_TOP = 903  # Top line position from example.ass
RUBY_Y_OFFSET = -47  # How much higher the ruby text should be

# Color mapping for common colors (matching example.ass)
COLOR_MAP = {
    "red": "&H0000FF&",
    "blue": "&HFF0000&",
    "green": "&H00FF00&",
    "yellow": "&H00FFFF&",
    "cyan": "&HFFFF00&",
    "magenta": "&HFF00FF&",
    "white": "&HFFFFFF&",
    "black": "&H000000&",
    # Special colors from example.ass
    "lightblue": "&H008AE6&",
    "darkblue": "&H0000E6&",
    "purple": "&HE600AC&",
    "orange": "&HE65C00&",
    "darkgreen": "&H2B8000&"
}

# Initialize the furigana generator
furigana_generator = FuriganaGenerator()

def extract_furigana_pairs(text, auto_generate=False):
    """
    Extract pairs of base text and furigana.
    
    Args:
        text (str): Original text
        auto_generate (bool): Whether to use automatic furigana generation
        
    Returns:
        list: List of tuples (base_text, furigana, is_kanji)
    """
    # First, handle any HTML color tags by temporarily replacing them
    color_placeholders = {}
    color_counter = 0
    
    def replace_color_tag(match):
        nonlocal color_counter
        placeholder = f"__COLOR_{color_counter}__"
        color_placeholders[placeholder] = match.group(0)
        color_counter += 1
        return placeholder
    
    # Replace color tags with placeholders
    text_with_placeholders = re.sub(r'<font color="[^"]+">(.*?)</font>', replace_color_tag, text)
    
    if auto_generate:
        # Use the furigana generator to add furigana
        text_with_furigana = furigana_generator.generate(text_with_placeholders)
        # Extract pairs from the generated format
        pattern = r'(\S+?)\{([^}]+)\}'
        
        # Find all matches
        matches = re.finditer(pattern, text_with_furigana)
        
        # Process the text
        pairs = []
        last_end = 0
        
        for match in matches:
            # Add any text before this match
            if match.start() > last_end:
                prefix = text_with_furigana[last_end:match.start()]
                for char in prefix:
                    # Restore color tags if present
                    if f"__COLOR_{len(pairs)}" in color_placeholders:
                        char = color_placeholders[f"__COLOR_{len(pairs)}"]
                    pairs.append((char, None, False))
            
            # Add the kanji with furigana
            base = match.group(1)
            furigana = match.group(2)
            
            # Restore color tags if present
            for placeholder, color_tag in color_placeholders.items():
                if placeholder in base:
                    base = base.replace(placeholder, color_tag)
            
            pairs.append((base, furigana, True))
            
            last_end = match.end()
        
        # Add any remaining text
        if last_end < len(text_with_furigana):
            suffix = text_with_furigana[last_end:]
            # Remove any remaining curly braces
            suffix = re.sub(r'\{[^}]+\}', '', suffix)
            for char in suffix:
                # Restore color tags if present
                if f"__COLOR_{len(pairs)}" in color_placeholders:
                    char = color_placeholders[f"__COLOR_{len(pairs)}"]
                pairs.append((char, None, False))
        
        return pairs
    else:
        # Extract manually added furigana in parentheses
        pattern = r'(\S+?)\(([^)]+)\)'
        
        # Find all matches
        matches = re.finditer(pattern, text_with_placeholders)
        
        # Process the text
        pairs = []
        last_end = 0
        
        for match in matches:
            # Add any text before this match
            if match.start() > last_end:
                prefix = text_with_placeholders[last_end:match.start()]
                for i, char in enumerate(prefix):
                    # Check if this position has a color placeholder
                    placeholder = f"__COLOR_{len(pairs)}"
                    if placeholder in color_placeholders:
                        char = color_placeholders[placeholder]
                    pairs.append((char, None, False))
            
            # Add the kanji with furigana
            base = match.group(1)
            furigana = match.group(2)
            
            # Restore color tags if present
            for placeholder, color_tag in color_placeholders.items():
                if placeholder in base:
                    base = base.replace(placeholder, color_tag)
            
            pairs.append((base, furigana, True))
            
            last_end = match.end()
        
        # Add any remaining text
        if last_end < len(text_with_placeholders):
            suffix = text_with_placeholders[last_end:]
            for i, char in enumerate(suffix):
                # Check if this position has a color placeholder
                placeholder = f"__COLOR_{len(pairs)}"
                if placeholder in color_placeholders:
                    char = color_placeholders[placeholder]
                pairs.append((char, None, False))
        
        return pairs

def create_advanced_ass_from_srt(
    srt_file_path, 
    output_dir=None,
    font=DEFAULT_FONT,
    font_size=DEFAULT_FONT_SIZE,
    ruby_font_size=DEFAULT_RUBY_FONT_SIZE,
    text_color=DEFAULT_TEXT_COLOR,
    ruby_color=DEFAULT_RUBY_COLOR,
    outline_color=DEFAULT_OUTLINE_COLOR,
    shadow_color=DEFAULT_SHADOW_COLOR,
    outline_size=DEFAULT_OUTLINE_SIZE,
    shadow_size=DEFAULT_SHADOW_SIZE,
    auto_generate_furigana=False
):
    """
    Convert an SRT file to ASS format with advanced styling and positioning.
    
    This creates separate dialogue entries for each text element with precise
    positioning, similar to professional anime subtitles.
    
    Args:
        srt_file_path (str): Path to the SRT file
        output_dir (str, optional): Directory to save the ASS file. Defaults to same directory as SRT.
        font (str, optional): Font name. Defaults to "MS Gothic".
        font_size (int, optional): Font size for main text. Defaults to 48.
        ruby_font_size (int, optional): Font size for ruby text. Defaults to 24.
        text_color (str, optional): Color for main text in ASS format. Defaults to "&H00FFFFFF".
        ruby_color (str, optional): Color for ruby text in ASS format. Defaults to "&H00FFFFFF".
        outline_color (str, optional): Color for text outline in ASS format. Defaults to "&H00000000".
        shadow_color (str, optional): Color for text shadow in ASS format. Defaults to "&H00000000".
        outline_size (int, optional): Size of text outline. Defaults to 2.
        shadow_size (int, optional): Size of text shadow. Defaults to 2.
        auto_generate_furigana (bool, optional): Whether to automatically generate furigana. Defaults to False.
        
    Returns:
        str: Path to the created ASS file
    """
    try:
        # Convert path to Path object
        srt_path = Path(srt_file_path)
        
        # Determine output directory and filename
        if output_dir is None:
            output_dir = srt_path.parent
        else:
            output_dir = Path(output_dir)
            
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output filename
        output_file = output_dir / f"{srt_path.stem}.ass"
        
        # Load the SRT file
        subs = pysubs2.load(str(srt_path), encoding="utf-8")
        
        # Create a new ASS file
        ass_subs = pysubs2.SSAFile()
        
        # Script info section
        ass_subs.info["Title"] = "Migaku Parsed"
        ass_subs.info["PlayResX"] = "1920"
        ass_subs.info["PlayResY"] = "1080"
        ass_subs.info["ScriptType"] = "v4.00+"
        
        # Create styles
        default_style = pysubs2.SSAStyle(
            fontname=font,
            fontsize=font_size,
            primarycolor=text_color,
            secondarycolor=text_color,
            outlinecolor=outline_color,
            backcolor=shadow_color,
            outline=outline_size,
            shadow=shadow_size,
            marginl=0,
            marginr=0,
            marginv=0,
            alignment=5  # Center-middle alignment
        )
        
        ruby_style = pysubs2.SSAStyle(
            fontname=font,
            fontsize=ruby_font_size,
            primarycolor=ruby_color,
            secondarycolor=ruby_color,
            outlinecolor=outline_color,
            backcolor=shadow_color,
            outline=outline_size,
            shadow=shadow_size,
            marginl=0,
            marginr=0,
            marginv=0,
            alignment=5  # Center-middle alignment
        )
        
        underline_style = pysubs2.SSAStyle(
            fontname=font,
            fontsize=font_size,
            primarycolor="&H4E4EF1&",  # Underline color from example.ass
            secondarycolor="&H4E4EF1&",
            outline=0,
            shadow=0,
            alignment=7  # Left-top alignment for positioning
        )
        
        highlight_style = pysubs2.SSAStyle(
            fontname=font,
            fontsize=font_size,
            primarycolor=text_color,
            secondarycolor=text_color,
            outlinecolor=outline_color,
            backcolor=shadow_color,
            outline=0,
            shadow=0,
            alignment=7  # Left-top alignment
        )
        
        # Add styles to the subtitle file
        ass_subs.styles["Default"] = default_style
        ass_subs.styles["Ruby"] = ruby_style
        ass_subs.styles["Underline"] = underline_style
        ass_subs.styles["Highlight"] = highlight_style
        
        # Process each subtitle
        for sub in subs:
            # Extract furigana pairs from the text
            pairs = extract_furigana_pairs(sub.text, auto_generate_furigana)
            
            # Calculate total width of text for centering
            total_width = sum(len(base) for base, _, _ in pairs) * font_size / 2
            
            # Base position for this subtitle line (centered horizontally)
            base_x = 960 - (total_width / 2)  # 960 is center of 1920 width
            base_y = 1011  # Bottom line position from example.ass
            ruby_y = 964   # Ruby position from example.ass
            
            # For multi-line subtitles, use different Y positions
            if "\n" in sub.text:
                # First line is higher
                base_y = 903
                ruby_y = 856
            
            current_x = base_x
            
            # Layer counter for proper stacking (higher numbers are on top)
            layer = 3  # Main text layer
            ruby_layer = 2  # Ruby text layer
            underline_layer = 1  # Underline layer
            
            # Process each pair
            for i, (base, furigana, is_kanji) in enumerate(pairs):
                # Calculate width of this text segment
                char_width = font_size / 2
                segment_width = len(base) * char_width
                
                # Convert HTML color tags to ASS color tags
                if "<font color=" in base:
                    color_match = re.search(r'<font color="([^"]+)">', base)
                    if color_match:
                        color = color_match.group(1)
                        # Convert HTML color to ASS color
                        if color.startswith('#'):
                            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
                        else:
                            # Map common color names to ASS colors
                            ass_color = COLOR_MAP.get(color.lower(), text_color)
                        
                        # Replace the HTML tag with ASS color tag
                        base = re.sub(r'<font color="[^"]+">(.*?)</font>', r'\1', base)
                        color_tag = f"{{\\c{ass_color}}}"
                    else:
                        color_tag = ""
                else:
                    color_tag = ""
                
                # Add main text dialogue
                pos_tag_main = f"{{\\pos({int(current_x)},{base_y})}}"
                close_color = "{\\c}" if color_tag else ""
                
                main_dialogue = pysubs2.SSAEvent(
                    start=sub.start,
                    end=sub.end,
                    style="Default",
                    layer=layer,
                    text=f"{pos_tag_main}{color_tag}{base}{close_color}"
                )
                ass_subs.events.append(main_dialogue)
                
                # Add ruby text if present
                if furigana:
                    pos_tag_ruby = f"{{\\pos({int(current_x)},{ruby_y})}}"
                    
                    ruby_dialogue = pysubs2.SSAEvent(
                        start=sub.start,
                        end=sub.end,
                        style="Ruby",
                        layer=ruby_layer,
                        text=f"{pos_tag_ruby}{color_tag}{furigana}{close_color}"
                    )
                    ass_subs.events.append(ruby_dialogue)
                    
                    # Add underline for kanji with furigana (using drawing commands as in example.ass)
                    pos_tag = "{\\pos(0,0)}"
                    color_tag = "{\\c&H4E4EF1&}"
                    p1_tag = "{\\p1}"
                    p0_tag = "{\\p0}"
                    c_tag = "{\\c}"
                    
                    underline_dialogue = pysubs2.SSAEvent(
                        start=sub.start,
                        end=sub.end,
                        style="Underline",
                        layer=underline_layer,
                        text=f"{pos_tag}{color_tag}{p1_tag}m {int(current_x - segment_width/4)} {base_y + 37} l {int(current_x + segment_width/4 + segment_width/2)} {base_y + 37} {int(current_x + segment_width/4 + segment_width/2)} {base_y + 41} {int(current_x - segment_width/4)} {base_y + 41}{p0_tag}{c_tag}"
                    )
                    ass_subs.events.append(underline_dialogue)
                
                # Move to the next position
                current_x += segment_width
        
        # Save as ASS file
        ass_subs.save(str(output_file))
        
        return str(output_file)
        
    except Exception as e:
        print(f"Error converting {srt_file_path} to ASS: {e}")
        raise

def create_ass_from_srt(
    srt_file_path, 
    output_dir=None,
    font=DEFAULT_FONT,
    font_size=DEFAULT_FONT_SIZE,
    ruby_font_size=DEFAULT_RUBY_FONT_SIZE,
    text_color=DEFAULT_TEXT_COLOR,
    ruby_color=DEFAULT_RUBY_COLOR,
    outline_color=DEFAULT_OUTLINE_COLOR,
    shadow_color=DEFAULT_SHADOW_COLOR,
    outline_size=DEFAULT_OUTLINE_SIZE,
    shadow_size=DEFAULT_SHADOW_SIZE,
    auto_generate_furigana=False,
    advanced_styling=True
):
    """
    Convert an SRT file to ASS format with ruby text support.
    
    Args:
        srt_file_path (str): Path to the SRT file
        output_dir (str, optional): Directory to save the ASS file. Defaults to same directory as SRT.
        font (str, optional): Font name. Defaults to "MS Gothic".
        font_size (int, optional): Font size for main text. Defaults to 48.
        ruby_font_size (int, optional): Font size for ruby text. Defaults to 24.
        text_color (str, optional): Color for main text in ASS format. Defaults to "&H00FFFFFF".
        ruby_color (str, optional): Color for ruby text in ASS format. Defaults to "&H00FFFFFF".
        outline_color (str, optional): Color for text outline in ASS format. Defaults to "&H00000000".
        shadow_color (str, optional): Color for text shadow in ASS format. Defaults to "&H00000000".
        outline_size (int, optional): Size of text outline. Defaults to 2.
        shadow_size (int, optional): Size of text shadow. Defaults to 2.
        auto_generate_furigana (bool, optional): Whether to automatically generate furigana. Defaults to False.
        advanced_styling (bool, optional): Whether to use advanced styling with separate dialogue entries. Defaults to True.
        
    Returns:
        str: Path to the created ASS file
    """
    if advanced_styling:
        return create_advanced_ass_from_srt(
            srt_file_path=srt_file_path,
            output_dir=output_dir,
            font=font,
            font_size=font_size,
            ruby_font_size=ruby_font_size,
            text_color=text_color,
            ruby_color=ruby_color,
            outline_color=outline_color,
            shadow_color=shadow_color,
            outline_size=outline_size,
            shadow_size=shadow_size,
            auto_generate_furigana=auto_generate_furigana
        )
    
    # Original implementation for simple ASS files with \rt tags
    try:
        # Convert path to Path object
        srt_path = Path(srt_file_path)
        
        # Determine output directory and filename
        if output_dir is None:
            output_dir = srt_path.parent
        else:
            output_dir = Path(output_dir)
            
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output filename
        output_file = output_dir / f"{srt_path.stem}.ass"
        
        # Load the SRT file
        subs = pysubs2.load(str(srt_path), encoding="utf-8")
        
        # Create styles
        default_style = pysubs2.SSAStyle(
            fontname=font,
            fontsize=font_size,
            primarycolor=text_color,
            secondarycolor=text_color,
            outlinecolor=outline_color,
            backcolor=shadow_color,
            outline=outline_size,
            shadow=shadow_size,
            marginl=20,
            marginr=20,
            marginv=20
        )
        
        ruby_style = pysubs2.SSAStyle(
            fontname=font,
            fontsize=ruby_font_size,
            primarycolor=ruby_color,
            secondarycolor=ruby_color,
            outlinecolor=outline_color,
            backcolor=shadow_color,
            outline=outline_size,
            shadow=shadow_size,
            marginl=20,
            marginr=20,
            marginv=20
        )
        
        # Add styles to the subtitle file
        subs.styles["Default"] = default_style
        subs.styles["Ruby"] = ruby_style
        
        # Process each line to add ruby tags
        for line in subs:
            if auto_generate_furigana:
                # Use the furigana generator to add furigana
                text_with_furigana = furigana_generator.generate(line.text)
                # Convert the generated format to ASS format
                line.text = convert_furigana_format_to_ass(text_with_furigana)
            else:
                # Use the existing method for manually added furigana in parentheses
                line.text = add_ruby_tags(line.text)
        
        # Save as ASS file
        subs.save(str(output_file), format_="ass")
        
        return str(output_file)
        
    except Exception as e:
        print(f"Error converting {srt_file_path} to ASS: {e}")
        raise

def add_ruby_tags(text):
    """
    Convert text with furigana in parentheses to ASS ruby format.
    
    Example:
    "漢字(かんじ)" becomes "{\\k0}漢字{\\rt(かんじ)}"
    
    Args:
        text (str): Text with furigana in parentheses
        
    Returns:
        str: Text with ASS ruby tags
    """
    def replace_with_ruby(match):
        base = match.group(1)  # The kanji/base text
        ruby = match.group(2)  # The furigana/ruby text
        return f"{{\\k0}}{base}{{\\rt({ruby})}}"
    
    # Pattern to match text with furigana in parentheses
    pattern = r'(\S+?)\(([^)]+)\)'
    
    # Replace all occurrences
    return re.sub(pattern, replace_with_ruby, text)

def convert_furigana_format_to_ass(text):
    """
    Convert text with furigana in curly braces (from furigana generator) to ASS ruby format.
    
    Example:
    "漢字{かんじ}" becomes "{\\k0}漢字{\\rt(かんじ)}"
    
    Args:
        text (str): Text with furigana in curly braces
        
    Returns:
        str: Text with ASS ruby tags
    """
    def replace_with_ruby(match):
        base = match.group(1)  # The kanji/base text
        ruby = match.group(2)  # The furigana/ruby text
        return f"{{\\k0}}{base}{{\\rt({ruby})}}"
    
    # Pattern to match text with furigana in curly braces
    pattern = r'(\S+?)\{([^}]+)\}'
    
    # Replace all occurrences
    return re.sub(pattern, replace_with_ruby, text)

def process_directory(
    input_dir, 
    output_dir=None, 
    auto_generate_furigana=False,
    advanced_styling=True,
    **style_kwargs
):
    """
    Process all SRT files in a directory and convert them to ASS format.
    
    Args:
        input_dir (str): Directory containing SRT files
        output_dir (str, optional): Directory to save ASS files. Defaults to input_dir.
        auto_generate_furigana (bool, optional): Whether to automatically generate furigana. Defaults to False.
        advanced_styling (bool, optional): Whether to use advanced styling with separate dialogue entries. Defaults to True.
        **style_kwargs: Style parameters to pass to create_ass_from_srt
        
    Returns:
        list: List of paths to created ASS files
    """
    input_path = Path(input_dir)
    
    if output_dir is None:
        output_dir = input_path
    else:
        output_dir = Path(output_dir)
        
    # Find all SRT files
    srt_files = list(input_path.glob("*.srt"))
    
    print(f"Found {len(srt_files)} SRT files in {input_dir}")
    
    # Convert each file
    output_files = []
    for srt_file in srt_files:
        try:
            output_file = create_ass_from_srt(
                srt_file_path=str(srt_file),
                output_dir=str(output_dir),
                auto_generate_furigana=auto_generate_furigana,
                advanced_styling=advanced_styling,
                **style_kwargs
            )
            print(f"Converted {srt_file.name} to {Path(output_file).name}")
            output_files.append(output_file)
        except Exception as e:
            print(f"Error processing {srt_file}: {e}")
            
    return output_files 