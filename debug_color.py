#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from src.utils.ass_converter import create_ass_from_srt

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create test directory if it doesn't exist
test_dir = Path("test_subs")
test_dir.mkdir(exist_ok=True)

# Create a test SRT file with color tags
test_srt_path = test_dir / "test_color_debug.srt"
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
    
    # Print the first few lines of the ASS file
    with open(output_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        dialogue_lines = [line for line in lines if line.startswith("Dialogue:")]
        logger.info(f"Found {len(dialogue_lines)} dialogue lines")
        logger.info("First 20 dialogue lines:")
        for i, line in enumerate(dialogue_lines[:20]):
            logger.info(f"{i+1}: {line.strip()}")
            
        # Check for color tags in the dialogue lines
        color_lines = [line for line in dialogue_lines if "\\c&H" in line]
        logger.info(f"Found {len(color_lines)} dialogue lines with color tags")
        if color_lines:
            logger.info("First 5 dialogue lines with color tags:")
            for i, line in enumerate(color_lines[:5]):
                logger.info(f"{i+1}: {line.strip()}")
        else:
            logger.warning("No color tags found in dialogue lines!")
            
except Exception as e:
    logger.error(f"Error converting SRT to ASS: {e}", exc_info=True) 