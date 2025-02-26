#!/usr/bin/env python3
"""
ASS Converter Utility

This module provides functionality to convert SRT subtitle files to ASS format
with proper ruby text (furigana) support for Japanese text, matching the format
used in professional anime subtitles with precise positioning and styling.
"""

import os
import re
import logging
from pathlib import Path
import pysubs2
from .furigana_generator import FuriganaGenerator

# Set up logging
logger = logging.getLogger(__name__)

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
    # First, handle any HTML color tags by directly converting them to ASS color tags
    def convert_html_to_ass_color(match):
        color = match.group(1)
        content = match.group(2)
        
        # Convert HTML color to ASS color
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
        else:
            # Map common color names to ASS colors
            ass_color = COLOR_MAP.get(color.lower(), "&H00FFFFFF&")
        
        # Create ASS color tag
        return f"{{\\c{ass_color}}}{content}{{\\c}}"
    
    # Replace HTML color tags with ASS color tags
    text_with_ass_colors = re.sub(r'<font color="([^"]+)">(.*?)</font>', convert_html_to_ass_color, text)
    
    if auto_generate:
        # Use the furigana generator to add furigana
        text_with_furigana = furigana_generator.generate(text_with_ass_colors)
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
                    pairs.append((char, None, False))
            
            # Add the kanji with furigana
            base = match.group(1)
            furigana = match.group(2)
            pairs.append((base, furigana, True))
            
            last_end = match.end()
        
        # Add any remaining text
        if last_end < len(text_with_furigana):
            suffix = text_with_furigana[last_end:]
            # Remove any remaining curly braces
            suffix = re.sub(r'\{[^}]+\}', '', suffix)
            for char in suffix:
                pairs.append((char, None, False))
        
        return pairs
    else:
        # Extract manually added furigana in parentheses
        pattern = r'(\S+?)\(([^)]+)\)'
        
        # Find all matches
        matches = re.finditer(pattern, text_with_ass_colors)
        
        # Process the text
        pairs = []
        last_end = 0
        
        for match in matches:
            # Add any text before this match
            if match.start() > last_end:
                prefix = text_with_ass_colors[last_end:match.start()]
                
                # Handle ASS color tags in the prefix
                i = 0
                while i < len(prefix):
                    if prefix[i:].startswith("{\\c"):
                        # Find the end of the color tag
                        end_idx = prefix.find("}", i)
                        if end_idx != -1:
                            # Extract the color tag
                            color_tag = prefix[i:end_idx+1]
                            # Skip the color tag
                            i = end_idx + 1
                            # Add the color tag as a separate pair
                            pairs.append((color_tag, None, False))
                            continue
                    elif prefix[i:].startswith("{\\c}"):
                        # End of color tag
                        pairs.append(("{\\c}", None, False))
                        i += 4
                        continue
                    
                    # Add the character
                    pairs.append((prefix[i], None, False))
                    i += 1
            
            # Add the kanji with furigana
            base = match.group(1)
            furigana = match.group(2)
            
            # Handle ASS color tags in the base text
            processed_base = ""
            i = 0
            while i < len(base):
                if base[i:].startswith("{\\c"):
                    # Find the end of the color tag
                    end_idx = base.find("}", i)
                    if end_idx != -1:
                        # Extract the color tag
                        color_tag = base[i:end_idx+1]
                        # Add the color tag to the processed base
                        processed_base += color_tag
                        # Skip the color tag
                        i = end_idx + 1
                        continue
                elif base[i:].startswith("{\\c}"):
                    # End of color tag
                    processed_base += "{\\c}"
                    i += 4
                    continue
                
                # Add the character
                processed_base += base[i]
                i += 1
            
            pairs.append((processed_base, furigana, True))
            
            last_end = match.end()
        
        # Add any remaining text
        if last_end < len(text_with_ass_colors):
            suffix = text_with_ass_colors[last_end:]
            
            # Handle ASS color tags in the suffix
            i = 0
            while i < len(suffix):
                if suffix[i:].startswith("{\\c"):
                    # Find the end of the color tag
                    end_idx = suffix.find("}", i)
                    if end_idx != -1:
                        # Extract the color tag
                        color_tag = suffix[i:end_idx+1]
                        # Skip the color tag
                        i = end_idx + 1
                        # Add the color tag as a separate pair
                        pairs.append((color_tag, None, False))
                        continue
                elif suffix[i:].startswith("{\\c}"):
                    # End of color tag
                    pairs.append(("{\\c}", None, False))
                    i += 4
                    continue
                
                # Add the character
                pairs.append((suffix[i], None, False))
                i += 1
        
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
        logger.debug(f"Starting conversion of {srt_file_path} to ASS format")
        
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
        logger.debug(f"Loading SRT file: {srt_path}")
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
        
        # Character width calculation constants
        # These values are based on typical character width ratios in Japanese fonts
        CHAR_WIDTH_RATIO = {
            'CJK': 1.0,      # Full-width CJK characters
            'LATIN': 0.5,    # Half-width Latin characters
            'DIGIT': 0.5,    # Digits
            'PUNCT': 0.5,    # Punctuation
            'SPACE': 0.5     # Space
        }
        
        # Function to estimate character width based on character type
        def estimate_char_width(char, base_width):
            if ord(char) >= 0x3000:  # CJK characters and full-width forms
                return base_width * CHAR_WIDTH_RATIO['CJK']
            elif char.isalpha():     # Latin alphabet
                return base_width * CHAR_WIDTH_RATIO['LATIN']
            elif char.isdigit():     # Digits
                return base_width * CHAR_WIDTH_RATIO['DIGIT']
            elif char.isspace():     # Spaces
                return base_width * CHAR_WIDTH_RATIO['SPACE']
            else:                    # Punctuation and others
                return base_width * CHAR_WIDTH_RATIO['PUNCT']
        
        # Function to calculate text width
        def calculate_text_width(text, char_base_width):
            # Remove HTML tags for width calculation
            clean_text = re.sub(r'<[^>]+>', '', text)
            return sum(estimate_char_width(char, char_base_width) for char in clean_text)
        
        # Spacing constants
        CHAR_BASE_WIDTH = font_size * 0.8  # Base width for character sizing
        RUBY_BASE_WIDTH = ruby_font_size * 0.8  # Base width for ruby character sizing
        CHAR_SPACING = font_size * 0.2  # Space between characters
        RUBY_SPACING = ruby_font_size * 0.2  # Space between ruby characters
        VERTICAL_SPACING = font_size * 1.5  # Vertical spacing between lines
        
        # Process each subtitle
        for sub in subs:
            logger.debug(f"Processing subtitle: {sub.text}")
            
            # Extract furigana pairs from the text
            pairs = extract_furigana_pairs(sub.text, auto_generate_furigana)
            logger.debug(f"Extracted pairs: {pairs}")
            
            # Calculate total width for centering
            total_width = 0
            for base, furigana, _ in pairs:
                base_width = calculate_text_width(base, CHAR_BASE_WIDTH)
                furigana_width = calculate_text_width(furigana, RUBY_BASE_WIDTH) if furigana else 0
                # Use the wider of the two for positioning
                segment_width = max(base_width, furigana_width) + CHAR_SPACING
                total_width += segment_width
            
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
                base_width = calculate_text_width(base, CHAR_BASE_WIDTH)
                furigana_width = calculate_text_width(furigana, RUBY_BASE_WIDTH) if furigana else 0
                
                # Use the wider of the two for positioning
                segment_width = max(base_width, furigana_width)
                
                # Calculate center position for this segment
                segment_center_x = current_x + (segment_width / 2)
                
                # Add main text dialogue
                pos_tag_main = f"{{\\pos({int(segment_center_x)},{base_y})}}"
                
                # Process color tags in the base text
                processed_text = base
                
                # Check if there are font color tags in the text
                if "<font color=" in processed_text:
                    logger.debug(f"Found color tags in text: {processed_text}")
                    # Extract all color tags
                    color_matches = list(re.finditer(r'<font color="([^"]+)">(.*?)</font>', processed_text))
                    
                    # Process each match from end to beginning to avoid index issues
                    for match in reversed(color_matches):
                        color = match.group(1)
                        content = match.group(2)
                        logger.debug(f"Processing color tag: color={color}, content={content}")
                        
                        # Convert HTML color to ASS color
                        if color.startswith('#'):
                            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
                        else:
                            # Map common color names to ASS colors
                            ass_color = COLOR_MAP.get(color.lower(), text_color)
                        
                        logger.debug(f"Converted color to ASS format: {ass_color}")
                        
                        # Create ASS color tag
                        color_tag_start = f"{{\\c{ass_color}}}"
                        color_tag_end = "{\\c}"
                        
                        # Replace the HTML tag with ASS color tag
                        processed_text = processed_text[:match.start()] + color_tag_start + content + color_tag_end + processed_text[match.end():]
                        logger.debug(f"Processed text with color tags: {processed_text}")
                
                # Escape curly braces in the processed text to avoid pysubs2 interpreting them as tags
                # This is necessary because pysubs2 will try to parse any curly braces as ASS tags
                final_text = pos_tag_main + processed_text
                
                main_dialogue = pysubs2.SSAEvent(
                    start=sub.start,
                    end=sub.end,
                    style="Default",
                    layer=layer,
                    text=final_text
                )
                ass_subs.events.append(main_dialogue)
                logger.debug(f"Added main dialogue: {main_dialogue.text}")
                
                # Add ruby text if present
                if furigana:
                    # Center ruby text above the base text
                    ruby_center_x = segment_center_x
                    pos_tag_ruby = f"{{\\pos({int(ruby_center_x)},{ruby_y})}}"
                    
                    # Process color tags for ruby text (use same color as base text if colored)
                    processed_ruby = furigana
                    
                    # Check if there are font color tags in the base text
                    if "<font color=" in base:
                        logger.debug(f"Found color tags in base text for ruby: {base}")
                        # Extract the first color tag
                        color_match = re.search(r'<font color="([^"]+)">', base)
                        if color_match:
                            color = color_match.group(1)
                            logger.debug(f"Applying color {color} to ruby text")
                            
                            # Convert HTML color to ASS color
                            if color.startswith('#'):
                                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                                ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
                            else:
                                # Map common color names to ASS colors
                                ass_color = COLOR_MAP.get(color.lower(), ruby_color)
                            
                            # Apply color to ruby text
                            processed_ruby = f"{{\\c{ass_color}}}{furigana}{{\\c}}"
                            logger.debug(f"Processed ruby text with color: {processed_ruby}")
                    
                    ruby_dialogue = pysubs2.SSAEvent(
                        start=sub.start,
                        end=sub.end,
                        style="Ruby",
                        layer=ruby_layer,
                        text=f"{pos_tag_ruby}{processed_ruby}"
                    )
                    ass_subs.events.append(ruby_dialogue)
                    logger.debug(f"Added ruby dialogue: {ruby_dialogue.text}")
                    
                    # Add underline for kanji with furigana
                    # Calculate underline width based on the base text width
                    underline_width = base_width
                    underline_left = segment_center_x - (underline_width / 2)
                    underline_right = segment_center_x + (underline_width / 2)
                    
                    pos_tag = "{\\pos(0,0)}"
                    color_tag = "{\\c&H4E4EF1&}"
                    p1_tag = "{\\p1}"
                    p0_tag = "{\\p0}"
                    c_tag = "{\\c}"
                    
                    # Create underline with drawing commands
                    underline_dialogue = pysubs2.SSAEvent(
                        start=sub.start,
                        end=sub.end,
                        style="Underline",
                        layer=underline_layer,
                        text=f"{pos_tag}{color_tag}{p1_tag}m {int(underline_left)} {base_y + 37} l {int(underline_right)} {base_y + 37} {int(underline_right)} {base_y + 41} {int(underline_left)} {base_y + 41}{p0_tag}{c_tag}"
                    )
                    ass_subs.events.append(underline_dialogue)
                    logger.debug(f"Added underline dialogue: {underline_dialogue.text}")
                
                # Move to the next position with proper spacing
                current_x += segment_width + CHAR_SPACING
        
        # Save as ASS file
        logger.debug(f"Saving ASS file to {output_file}")
        ass_subs.save(str(output_file))
        
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Error converting {srt_file_path} to ASS: {e}", exc_info=True)
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