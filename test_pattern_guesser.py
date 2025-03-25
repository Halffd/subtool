#!/usr/bin/env python
# Test script for the pattern guesser functionality

import os
import sys
from pathlib import Path
import logging
from src.utils.pattern_guesser import suggest_patterns, check_for_japanese, group_files_by_pattern, create_patterns_from_japanese_groups, create_patterns_from_general_groups, detect_episode_patterns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PatternGuesserTest")

# Add src directory to path
src_path = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src_path))

# Import the pattern guesser
try:
    from utils.pattern_guesser import suggest_patterns
except ImportError:
    logger.error("Failed to import pattern_guesser module. Make sure you're running from the project root.")
    sys.exit(1)


def test_japanese_content_detection():
    """Test the Japanese content detection functionality."""
    test_dir = Path("test_subs")
    test_files = [
        "random_name_05.srt",
        "another_random_05.srt",
        "third_random_05.srt"
    ]
    
    logger.info("\nTesting Japanese content detection:")
    japanese_files = []
    
    for filename in test_files:
        file_path = test_dir / filename
        if file_path.exists():
            is_japanese, jp_percentage = check_for_japanese(file_path, logger)
            logger.info(f"{filename}: {jp_percentage:.2f}% Japanese characters - {'Japanese' if is_japanese else 'Not Japanese'}")
            if is_japanese:
                japanese_files.append(filename)
    
    return japanese_files


def test_pattern_guesser():
    """Test the pattern guesser with content-based Japanese detection."""
    # Get all subtitle files
    test_dir = Path("test_subs")
    files = list(test_dir.glob("*.srt"))
    
    # First detect Japanese files by content
    japanese_files = []
    for file in files:
        is_japanese, jp_percentage = check_for_japanese(file, logger)
        if is_japanese:
            japanese_files.append(str(file.name))
    
    logger.info(f"\nFound {len(files)} total files")
    logger.info(f"Detected {len(japanese_files)} Japanese files by content:")
    for jp_file in japanese_files:
        logger.info(f"  - {jp_file}")
    
    # Group files by pattern
    groups = group_files_by_pattern(files, japanese_files, logger)
    logger.info("\nFile groups:")
    for group_name, file_list in groups.items():
        logger.info(f"\n{group_name}:")
        for file in file_list:
            logger.info(f"  - {file}")
    
    # Create patterns from Japanese groups
    non_jp_files = [str(f.name) for f in files if str(f.name) not in japanese_files]
    jp_patterns = create_patterns_from_japanese_groups(groups, japanese_files, non_jp_files, logger)
    logger.info("\nPatterns from Japanese groups:")
    for key, value in jp_patterns.items():
        logger.info(f"{key}: {value}")
    
    # Create patterns from general groups
    general_patterns = create_patterns_from_general_groups(groups, [f.name for f in files], logger)
    logger.info("\nPatterns from general groups:")
    for key, value in general_patterns.items():
        logger.info(f"{key}: {value}")
    
    # Detect episode patterns
    episode_patterns = detect_episode_patterns(files, general_patterns, logger)
    logger.info("\nEpisode patterns:")
    for key, value in episode_patterns.items():
        logger.info(f"{key}: {value}")


def main():
    """Run a test of the pattern guesser on a directory."""
    # Check if a directory is provided as an argument
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # Use a default test directory if none is provided
        directory = input("Enter the path to a directory with subtitle files: ")
    
    # Make sure the directory exists
    if not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return
    
    logger.info(f"Testing pattern guesser on directory: {directory}")
    
    # Get suggestions
    result = suggest_patterns(directory, logger)
    
    # Print results
    if 'error' in result:
        logger.error(f"Error: {result['error']}")
        return
    
    logger.info("Pattern Analysis Results:")
    logger.info(f"File count: {result['file_count']}")
    
    patterns = result['suggested_patterns']
    verification = result['verification']
    
    logger.info("\nSuggested Patterns:")
    logger.info(f"Sub1 pattern: {patterns['sub1_pattern']}")
    logger.info(f"Sub2 pattern: {patterns['sub2_pattern']}")
    logger.info(f"Sub1 episode pattern: {patterns['sub1_ep_pattern']}")
    logger.info(f"Sub2 episode pattern: {patterns['sub2_ep_pattern']}")
    
    logger.info("\nVerification Results:")
    logger.info(f"Sub1 pattern matches: {verification['sub1_match_count']}/{result['file_count']} files")
    logger.info(f"Sub2 pattern matches: {verification['sub2_match_count']}/{result['file_count']} files")
    logger.info(f"Overlapping matches: {verification['overlap_count']}")
    logger.info(f"Sub1 episode extraction success: {verification['sub1_episode_extract_success']}/{verification['sub1_match_count'] or 1} matches")
    logger.info(f"Sub2 episode extraction success: {verification['sub2_episode_extract_success']}/{verification['sub2_match_count'] or 1} matches")
    
    # Print Japanese and English files
    logger.info("\nFile Groups:")
    logger.info(f"Japanese files: {result['japanese_file_count']}")
    for file in result['japanese_files'][:5]:  # Show first 5 files
        logger.info(f"  - {file}")
    if len(result['japanese_files']) > 5:
        logger.info(f"  - ... and {len(result['japanese_files']) - 5} more")
        
    logger.info(f"English files: {result['english_file_count']}")
    for file in result['english_files'][:5]:  # Show first 5 files
        logger.info(f"  - {file}")
    if len(result['english_files']) > 5:
        logger.info(f"  - ... and {len(result['english_files']) - 5} more")


if __name__ == "__main__":
    # First test Japanese content detection
    detected_jp_files = test_japanese_content_detection()
    
    # Then test full pattern guesser
    test_pattern_guesser() 