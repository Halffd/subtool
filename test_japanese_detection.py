#!/usr/bin/env python
# Test script for Japanese content detection in subtitle files

import os
import sys
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JapaneseDetectionTest")

# Add src directory to path
src_path = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src_path))

try:
    from utils.pattern_guesser import PatternGuesser
except ImportError:
    logger.error("Failed to import PatternGuesser module. Make sure you're running from the project root.")
    sys.exit(1)

def test_file(file_path):
    """Test a specific file for Japanese content detection."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    try:
        # Create a PatternGuesser instance
        guesser = PatternGuesser(logger)
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test if it has significant Japanese content
        is_japanese = guesser._is_japanese_content(content)
        
        # Output results
        logger.info(f"File: {file_path}")
        logger.info(f"Contains significant Japanese content (>30%): {is_japanese}")
        
        # If verbose mode, show character counts
        if len(sys.argv) > 2 and sys.argv[2].lower() == 'verbose':
            # Process the content exactly as in the pattern guesser
            # Remove SRT timestamps, numbers, and common symbols
            cleaned_content = re.sub(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+', '', content)
            cleaned_content = re.sub(r'^\d+$', '', cleaned_content, flags=re.MULTILINE)
            
            # Remove HTML tags
            cleaned_content = re.sub(r'<[^>]+>', '', cleaned_content)
            
            # Keep only actual text lines
            text_lines = [line for line in cleaned_content.split('\n') 
                         if line.strip() and not line.strip().isdigit()]
            
            if not text_lines:
                logger.info("No valid text lines found in file")
                return
            
            text_content = '\n'.join(text_lines)
            
            # Count characters
            total_chars = 0
            japanese_chars = 0
            
            for char in text_content:
                # Skip whitespace and punctuation
                if char.isspace() or char in '.,:;?!()[]{}"\'':
                    continue
                
                total_chars += 1
                
                # Check for Japanese character ranges
                # Hiragana (3040-309F), Katakana (30A0-30FF), CJK Unified Ideographs (4E00-9FFF)
                if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FFF':
                    japanese_chars += 1
            
            japanese_percentage = 0 if total_chars == 0 else (japanese_chars / total_chars) * 100
            logger.info(f"Total characters: {total_chars}")
            logger.info(f"Japanese characters: {japanese_chars}")
            logger.info(f"Japanese percentage: {japanese_percentage:.2f}%")
            logger.info(f"Decision threshold: >30%")
            
            # Show sample of Japanese characters found
            if japanese_chars > 0:
                japanese_samples = [
                    char for char in text_content if 
                    '\u3040' <= char <= '\u309F' or 
                    '\u30A0' <= char <= '\u30FF' or 
                    '\u4E00' <= char <= '\u9FFF'
                ]
                sample = ''.join(japanese_samples[:30])
                if len(sample) > 0:
                    logger.info(f"Sample Japanese characters: {sample}...")
    
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Run a test of the Japanese content detection on a specified file."""
    # Check if a file is provided as an argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        test_file(file_path)
    else:
        logger.error("Please provide a subtitle file path as an argument")
        logger.info("Usage: python test_japanese_detection.py path/to/subtitle.srt [verbose]")
        logger.info("Add 'verbose' for detailed character analysis")
        
if __name__ == "__main__":
    main() 