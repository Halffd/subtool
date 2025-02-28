#!/usr/bin/env python3
import os
import re
import logging
from pathlib import Path
import pysubs2
from src.utils.ass_converter import create_ass_from_srt

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_hex_color_conversion():
    """Test hex color conversion from HTML to ASS format."""
    test_cases = [
        ("#4B0082", "&H82004B&"),  # Indigo
        ("#FF4500", "&H0045FF&"),  # OrangeRed
        ("#228B22", "&H228B22&"),  # ForestGreen
        ("#9932CC", "&HCC3299&"),  # DarkOrchid
        ("#1E90FF", "&HFF901E&"),  # DodgerBlue
        ("#FFA500", "&H00A5FF&"),  # Orange
        ("#8B4513", "&H13458B&"),  # SaddleBrown
        ("#FFD700", "&H00D7FF&"),  # Gold
        ("#2F4F4F", "&H4F4F2F&"),  # DarkSlateGray
        ("#CD853F", "&H3F85CD&"),  # Peru
    ]
    
    logger.info("Testing hex color conversion...")
    for html_color, expected_ass in test_cases:
        # Convert HTML color to ASS color
        r, g, b = int(html_color[1:3], 16), int(html_color[3:5], 16), int(html_color[5:7], 16)
        ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
        
        if ass_color == expected_ass:
            logger.info(f"✓ {html_color} -> {ass_color}")
        else:
            logger.error(f"✗ {html_color} -> {ass_color} (expected {expected_ass})")

def test_color_tag_extraction():
    """Test extraction of color tags from text."""
    test_text = '<font color="#4B0082">藤色</font>の<font color="#FF4500">朱色</font>'
    logger.info(f"Testing color tag extraction from: {test_text}")
    
    color_matches = list(re.finditer(r'<font color="([^"]+)">(.*?)</font>', test_text))
    for match in color_matches:
        color = match.group(1)
        content = match.group(2)
        logger.info(f"Found color tag: color={color}, content={content}")
        
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
            logger.info(f"Converted to ASS color: {ass_color}")

def test_ass_conversion():
    """Test conversion of SRT with hex colors to ASS format."""
    test_file = "test_subs/test_hex_colors.srt"
    logger.info(f"Testing ASS conversion of {test_file}")
    
    try:
        output_file = create_ass_from_srt(
            test_file,
            auto_generate_furigana=False,
            advanced_styling=True
        )
        logger.info(f"Successfully created ASS file: {output_file}")
        
        # Read the ASS file
        with open(output_file, "r", encoding="utf-8") as f:
            ass_content = f.read()
        
        # Check for color tags (both formats)
        color_tags = re.findall(r'(?:\\c|\{\\c)&H[0-9A-F]+&(?:\})?', ass_content)
        logger.info(f"Found {len(color_tags)} color tags in ASS file")
        for i, tag in enumerate(color_tags):
            logger.info(f"Color tag {i+1}: {tag}")
        
        # Check for dialogue lines with color tags
        dialogue_lines = [line for line in ass_content.split('\n') 
                         if line.startswith('Dialogue:') and ('\\c&H' in line or '{\\c&H' in line)]
        logger.info(f"Found {len(dialogue_lines)} dialogue lines with color tags")
        for i, line in enumerate(dialogue_lines[:5]):
            logger.info(f"Dialogue line {i+1}: {line}")
            
        # Verify each color is properly converted
        test_colors = [
            "#4B0082", "#FF4500", "#228B22", "#9932CC", "#1E90FF",
            "#FFA500", "#8B4513", "#FFD700", "#2F4F4F", "#CD853F"
        ]
        for color in test_colors:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
            # Check for both formats
            if f"\\c{ass_color}" in ass_content or f"{{\\c{ass_color}}}" in ass_content:
                logger.info(f"✓ Found correctly converted color: {color} -> {ass_color}")
            else:
                logger.error(f"✗ Missing or incorrect color conversion: {color} -> {ass_color}")
                
    except Exception as e:
        logger.error(f"Error during ASS conversion: {e}", exc_info=True)

def main():
    """Run all hex color tests."""
    logger.info("Starting hex color tests...")
    
    # Run all tests
    test_hex_color_conversion()
    test_color_tag_extraction()
    test_ass_conversion()
    
    logger.info("Hex color tests completed")

if __name__ == "__main__":
    main() 