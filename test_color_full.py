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

# Create test directory if it doesn't exist
test_dir = Path("test_subs")
test_dir.mkdir(exist_ok=True)

# Create a test SRT file with color tags
test_srt_path = test_dir / "test_color_full.srt"
with open(test_srt_path, "w", encoding="utf-8") as f:
    f.write("""1
00:00:01,000 --> 00:00:05,000
<font color="blue">青い</font>空(そら)と<font color="red">赤い</font>夕日(ゆうひ)

2
00:00:06,000 --> 00:00:10,000
<font color="#00FF00">緑の</font>草原(そうげん)と<font color="#FF00FF">紫の</font>花(はな)

3
00:00:11,000 --> 00:00:15,000
<font color="darkblue">深い</font>海(うみ)と<font color="orange">オレンジ</font>色(いろ)の魚(さかな)
""")

logger.info(f"Created test SRT file at {test_srt_path}")

# Run the converter
try:
    output_file = create_ass_from_srt(
        str(test_srt_path),
        auto_generate_furigana=False,
        advanced_styling=True
    )
    logger.info(f"Successfully created ASS file at {output_file}")
    
    # Read the ASS file
    with open(output_file, "r", encoding="utf-8") as f:
        ass_content = f.read()
    
    # Check for color tags
    color_tags = re.findall(r'\\c&H[0-9A-F]+&', ass_content)
    logger.info(f"Found {len(color_tags)} color tags in the ASS file")
    for i, tag in enumerate(color_tags):
        logger.info(f"Color tag {i+1}: {tag}")
    
    # Check for dialogue lines
    dialogue_lines = re.findall(r'Dialogue: [^\n]+', ass_content)
    logger.info(f"Found {len(dialogue_lines)} dialogue lines in the ASS file")
    for i, line in enumerate(dialogue_lines[:10]):
        logger.info(f"Dialogue line {i+1}: {line}")
    
    # Check for dialogue lines with color tags
    color_dialogue_lines = [line for line in dialogue_lines if "\\c&H" in line]
    logger.info(f"Found {len(color_dialogue_lines)} dialogue lines with color tags")
    for i, line in enumerate(color_dialogue_lines[:5]):
        logger.info(f"Color dialogue line {i+1}: {line}")
    
    # If no color tags found in dialogue lines, this is an issue
    if not color_dialogue_lines:
        logger.warning("No color tags found in dialogue lines!")
        
        # Let's examine the extract_furigana_pairs function output
        from src.utils.ass_converter import extract_furigana_pairs
        
        # Test with a simple example
        test_text = '<font color="blue">青い</font>空(そら)と<font color="red">赤い</font>夕日(ゆうひ)'
        pairs = extract_furigana_pairs(test_text, auto_generate=False)
        logger.info(f"Extract furigana pairs output for test text: {pairs}")
        
        # Check if the pairs contain color tags
        color_pairs = [pair for pair in pairs if "<font color=" in pair[0]]
        logger.info(f"Found {len(color_pairs)} pairs with color tags")
        for i, pair in enumerate(color_pairs):
            logger.info(f"Color pair {i+1}: {pair}")
    
except Exception as e:
    logger.error(f"Error in test script: {e}", exc_info=True) 