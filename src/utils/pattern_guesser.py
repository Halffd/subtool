#!/usr/bin/env python
"""Pattern guesser utility for subtitle files."""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import unicodedata
import chardet

# Function to check if a character is Japanese (Hiragana, Katakana, or Kanji)
def is_japanese_char(char: str) -> bool:
    """Check if a character is Japanese."""
    name = unicodedata.name(char, '')
    return any(japanese_script in name for japanese_script in ['HIRAGANA', 'KATAKANA', 'CJK UNIFIED'])

def suggest_patterns(directory: str, logger=None) -> dict:
    """
    Analyze subtitle files in a directory and suggest patterns for filtering
    and episode number extraction.
    
    Args:
        directory: Path to directory containing subtitle files
        logger: Logger to use for debug output
        
    Returns:
        Dictionary containing:
        - suggested_patterns: dict with pattern suggestions
        - file_count: total number of srt files
        - verification: metrics about pattern quality
        - groups: detected subtitle groups
        - japanese_files: list of files with significant Japanese content (if any)
        - conflicts: dictionary of detected pattern conflicts
    """
    try:
        # Set up logging if not provided
        if logger is None:
            logger = logging.getLogger("pattern_guesser")
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
        
        # Find all SRT files in the directory
        dir_path = Path(directory)
        srt_files = list(dir_path.glob('*.srt'))
        
        if not srt_files:
            return {
                "error": "No .srt files found in directory",
                "file_count": 0,
                "suggested_patterns": {
                    "sub1_pattern": "",
                    "sub2_pattern": "",
                    "sub1_ep_pattern": "",
                    "sub2_ep_pattern": ""
                },
                "verification": {
                    "sub1_matches": 0,
                    "sub2_matches": 0,
                    "overlap": 0,
                    "sub1_ep_matches": 0,
                    "sub2_ep_matches": 0
                },
                "conflicts": {}
            }
            
        logger.info(f"Found {len(srt_files)} SRT files")
        
        # Step 1: Analyze files to identify Japanese content
        japanese_files = []
        non_japanese_files = []
        
        for file_path in srt_files:
            is_japanese, jp_percentage = check_for_japanese(file_path, logger)
            if is_japanese:
                japanese_files.append(file_path.name)
                logger.debug(f"File {file_path.name} identified as Japanese ({jp_percentage:.2f}% Japanese characters)")
            else:
                non_japanese_files.append(file_path.name)
                logger.debug(f"File {file_path.name} identified as non-Japanese ({jp_percentage:.2f}% Japanese characters)")
        
        # Step 2: Group files by patterns
        groups = group_files_by_pattern(srt_files, japanese_files, logger)
        
        # Step 3: Generate patterns based on detected groups
        suggested_patterns = {}
        
        if "Japanese_Content" in groups:
            # Use Japanese content detection to determine sub1 vs sub2
            suggested_patterns = create_patterns_from_japanese_groups(groups, japanese_files, non_japanese_files, logger)
        else:
            # Use other criteria (file naming conventions, etc)
            suggested_patterns = create_patterns_from_general_groups(groups, srt_files, logger)
        
        # Now let's specifically look for episode number patterns
        episode_patterns = detect_episode_patterns(srt_files, suggested_patterns, logger)
        suggested_patterns.update(episode_patterns)
        
        # Check for conflicts in patterns
        conflicts = detect_conflicts(srt_files, suggested_patterns, logger)
        
        # Verify the patterns with some metrics
        verification = verify_patterns(srt_files, suggested_patterns, japanese_files, logger)
        
        # Log results summary
        logger.info(f"Analysis complete. Found {len(conflicts)} pattern conflicts.")
        
        # Return the results
        return {
            "suggested_patterns": suggested_patterns,
            "file_count": len(srt_files),
            "verification": verification,
            "groups": groups,
            "japanese_files": japanese_files if japanese_files else None,
            "conflicts": conflicts
        }
        
    except Exception as e:
        import traceback
        error_str = f"Error analyzing files: {e}\n{traceback.format_exc()}"
        if logger:
            logger.error(error_str)
        return {
            "error": str(e),
            "file_count": len(srt_files) if 'srt_files' in locals() else 0,
            "suggested_patterns": {
                "sub1_pattern": "",
                "sub2_pattern": "",
                "sub1_ep_pattern": "",
                "sub2_ep_pattern": ""
            },
            "verification": {
                "sub1_matches": 0,
                "sub2_matches": 0,
                "overlap": 0,
                "sub1_ep_matches": 0,
                "sub2_ep_matches": 0
            },
            "conflicts": {}
        }

def check_for_japanese(file_path: Path, logger) -> Tuple[bool, float]:
    """
    Check if a file contains significant Japanese text.
    Returns (is_japanese, percentage_of_japanese_chars)
    """
    try:
        # Read the file with detection of encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)  # Read first 4KB to determine encoding
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # Read the file with detected encoding
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read(8192)  # Sample of file content
        
        # Count Japanese characters
        jp_chars = 0
        total_chars = 0
        
        # Regular expression for Japanese character ranges:
        # Hiragana, Katakana, and common Kanji ranges
        jp_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        
        for char in content:
            if not char.isspace() and not char.isdigit() and not char in '.,;:!?()-[]{}':
                total_chars += 1
                if jp_pattern.match(char):
                    jp_chars += 1
        
        if total_chars == 0:
            return False, 0.0
            
        jp_percentage = (jp_chars / total_chars) * 100
        
        # Consider it Japanese if more than 30% are Japanese characters
        return jp_percentage > 30.0, jp_percentage
        
    except Exception as e:
        logger.error(f"Error checking Japanese content in {file_path}: {e}")
        return False, 0.0

def group_files_by_pattern(files: List[Path], japanese_files: List[str], logger) -> Dict[str, List[str]]:
    """
    Group files by common patterns in their names.
    """
    groups = {}
    
    # First, group by Japanese content
    if japanese_files:
        groups["Japanese_Content"] = japanese_files
    
    # Group by common tokens in filenames
    token_patterns = {}
    
    for file in files:
        # Split filename into tokens
        tokens = re.split(r'[.\s\[\]\(\)_-]', file.stem.lower())
        tokens = [t for t in tokens if t and len(t) > 1]  # Remove empty and single-char tokens
        
        for token in tokens:
            if token not in token_patterns:
                token_patterns[token] = []
            token_patterns[token].append(file.name)
    
    # Filter for tokens that appear in multiple files
    for token, file_list in token_patterns.items():
        if len(file_list) > 1:
            groups[token] = file_list
    
    return groups

def create_patterns_from_japanese_groups(groups, jp_files, non_jp_files, logger):
    """Create patterns based on Japanese content detection"""
    # First find common base names without episode numbers
    base_names = {}
    episode_numbers = {}
    
    # Process all files to extract base names and episode numbers
    for file_list in [jp_files, non_jp_files]:
        for filename in file_list:
            # Skip already merged files
            if '.merged.srt' in filename or '-Sync.srt' in filename:
                continue
                
            # Try to find numbers that could be episode numbers
            number_match = re.search(r'(?:^|\D)(\d{1,3})(?:\D|$)', filename)
            if number_match:
                episode = number_match.group(1)
                # Get the parts before and after the number
                parts = re.split(r'\d{1,3}', filename, maxsplit=1)
                if len(parts) >= 2:
                    base_name = parts[0].strip('[] ._-')
                    if base_name not in base_names:
                        base_names[base_name] = {'jp': 0, 'non_jp': 0}
                    if filename in jp_files:
                        base_names[base_name]['jp'] += 1
                    else:
                        base_names[base_name]['non_jp'] += 1
                    
                    # Store episode number for this base name
                    if base_name not in episode_numbers:
                        episode_numbers[base_name] = set()
                    episode_numbers[base_name].add(episode)
    
    # Find the base name that appears most consistently in both groups
    best_base_name = None
    best_score = 0
    
    for base_name, counts in base_names.items():
        # Skip if we don't have episode numbers for this base name
        if base_name not in episode_numbers:
            continue
            
        # Score is based on having similar counts in both groups
        # and having multiple episode numbers
        jp_count = counts['jp']
        non_jp_count = counts['non_jp']
        episode_count = len(episode_numbers[base_name])
        
        if jp_count > 0 and non_jp_count > 0 and episode_count > 1:
            score = min(jp_count, non_jp_count) * episode_count
            if score > best_score:
                best_score = score
                best_base_name = base_name
    
    # If we found a good base name, create patterns
    if best_base_name:
        logger.info(f"Found matching base name: {best_base_name}")
        
        # For Japanese files, check multiple patterns
        jp_patterns = []
        if any('.ja[cc].srt' in f for f in jp_files):
            jp_patterns.append(r'\.ja\[cc\]\.srt$')
        if any('.jp.srt' in f for f in jp_files):
            jp_patterns.append(r'\.jp\.srt$')
        if any('.ja.srt' in f for f in jp_files):
            jp_patterns.append(r'\.ja\.srt$')
        if any('dialogue.srt' in f for f in jp_files):
            jp_patterns.append(r'\.dialogue\.srt$')
            
        # For English files, check multiple patterns
        en_patterns = []
        if any('.2.english.srt' in f for f in non_jp_files):
            en_patterns.append(r'\.2\.english\.srt$')
        if any('.en.srt' in f for f in non_jp_files):
            en_patterns.append(r'\.en\.srt$')
        if any('.eng.srt' in f for f in non_jp_files):
            en_patterns.append(r'\.eng\.srt$')
        if any('dialogue.srt' in f for f in non_jp_files):
            en_patterns.append(r'\.dialogue\.srt$')
        
        # Combine patterns with OR operator
        sub1_pattern = '|'.join(jp_patterns) if jp_patterns else r'\.ja(?:\[cc\])?\.srt$'
        sub2_pattern = '|'.join(en_patterns) if en_patterns else r'\.(?:en|eng|english)\.srt$'
        
        # Extract episode pattern based on file format
        if any('S01E' in f for f in jp_files + non_jp_files):
            ep_pattern = r'S01E(\d+)'
        elif any(' - ' in f and '[' in f for f in jp_files + non_jp_files):
            ep_pattern = r' - (\d+) \['
        else:
            ep_pattern = r'(\d{1,3})'
            
        return {
            "sub1_pattern": sub1_pattern,
            "sub2_pattern": sub2_pattern,
            "sub1_ep_pattern": ep_pattern,
            "sub2_ep_pattern": ep_pattern
        }
    
    # Fallback to simple patterns if no good base name found
    return {
        "sub1_pattern": r'\.(?:ja(?:\[cc\])?|jp|japanese)\.srt$',
        "sub2_pattern": r'\.(?:en|eng|english|2\.english)\.srt$',
        "sub1_ep_pattern": r'(?:S01E|E)?(\d{1,3})',
        "sub2_ep_pattern": r'(?:S01E|E)?(\d{1,3})'
    }

def create_patterns_from_general_groups(groups, all_files, logger):
    """Create patterns based on general file grouping"""
    # Find groups that could represent different subtitle types
    potential_groups = {}
    
    for group_name, files in groups.items():
        if len(files) >= 2:  # Needs at least two files to be a meaningful group
            # Skip very common tokens that appear in almost all files
            if len(files) > len(all_files) * 0.9:
                continue
            potential_groups[group_name] = files
    
    # Sort groups by size (number of files)
    sorted_groups = sorted(potential_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Take the top two groups as potential sub1 and sub2 groups
    if len(sorted_groups) >= 2:
        group1_name, group1_files = sorted_groups[0]
        group2_name, group2_files = sorted_groups[1]
        
        # Extract common tokens from each group
        group1_tokens = extract_common_tokens(group1_files)
        group2_tokens = extract_common_tokens(group2_files)
        
        sub1_pattern = '|'.join(group1_tokens)
        sub2_pattern = '|'.join(group2_tokens)
    else:
        # Not enough distinct groups, use fallbacks
        sub1_pattern = 'sub1|en|eng|english'
        sub2_pattern = 'sub2|ja|jpn|japanese'
    
    return {
        "sub1_pattern": sub1_pattern,
        "sub2_pattern": sub2_pattern
    }

def extract_common_tokens(file_names):
    """Extract common tokens/words from a list of filenames"""
    all_tokens = []
    
    for name in file_names:
        # Split by common delimiters and lowercase
        tokens = re.split(r'[.\s\[\]\(\)_-]', name.lower())
        tokens = [t for t in tokens if t and len(t) > 1 and not t.isdigit()]  # Remove empty, single-char, and pure digit tokens
        all_tokens.extend(tokens)
    
    # Count token frequencies
    token_counts = {}
    for token in all_tokens:
        if token not in token_counts:
            token_counts[token] = 0
        token_counts[token] += 1
    
    # Keep tokens that appear multiple times but not in nearly all files
    common_tokens = [token for token, count in token_counts.items() 
                   if count > 1 and count < len(file_names) * 0.9]
    
    # Sort by frequency
    common_tokens.sort(key=lambda x: token_counts[x], reverse=True)
    
    # Take top 15 tokens
    return common_tokens[:15]

def detect_episode_patterns(files, patterns, logger):
    """Detect episode number patterns in filenames."""
    # Known episode number formats to try
    episode_formats = [
        # For Japanese files (SxxExx format)
        (r'[Ss](\d+)[Ee](\d+)', "SxxExx format"),
        
        # For English files (various formats)
        (r'(?:^|\s|_|-)\s*(\d{1,2})\s*(?:\s|$|\]|\[)', "Number between delimiters"),
        (r'[\s._-](\d{1,2})(?:[\s._-]|$)', "Simple number"),
        (r'[Ee]p(?:isode)?[\s._-]*(\d{1,2})', "Episode format"),
        (r'(?:^|\s|_|-)\[?(\d{1,2})\]?(?:\s|$|\.)', "Bracketed number")
    ]
    
    # Find files matching each pattern
    sub1_files = [f for f in files if re.search(patterns.get('sub1_pattern', ''), f.name, re.IGNORECASE)]
    sub2_files = [f for f in files if re.search(patterns.get('sub2_pattern', ''), f.name, re.IGNORECASE)]
    
    def find_episode_pattern(file_group):
        if not file_group:
            return r'(\d{1,2})', 0
            
        # Count matches for each pattern
        pattern_matches = {}
        episode_numbers = {}
        
        for pattern, desc in episode_formats:
            matches = 0
            current_episodes = set()
            
            for file in file_group:
                match = re.search(pattern, file.name)
                if match:
                    # Get episode number from last group
                    ep_num = int(match.group(match.lastindex))
                    if 1 <= ep_num <= 99:  # Validate episode number
                        matches += 1
                        current_episodes.add(ep_num)
            
            if matches > 0:
                # Score based on sequential episodes and valid range
                episode_list = sorted(current_episodes)
                sequential_score = sum(1 for i in range(len(episode_list)-1) 
                                    if episode_list[i+1] == episode_list[i] + 1)
                pattern_matches[pattern] = (matches, sequential_score)
                episode_numbers[pattern] = current_episodes
        
        # Find best pattern
        best_pattern = None
        best_score = (-1, -1)  # (matches, sequential_score)
        
        for pattern, (matches, sequential_score) in pattern_matches.items():
            score = (matches, sequential_score)
            if score > best_score:
                best_score = score
                best_pattern = pattern
                
        return best_pattern or r'(\d{1,2})', best_score[0]
    
    # Find best patterns for each group
    sub1_ep_pattern, sub1_matches = find_episode_pattern(sub1_files)
    sub2_ep_pattern, sub2_matches = find_episode_pattern(sub2_files)
    
    logger.debug(f"Detected episode patterns - Sub1: {sub1_ep_pattern} ({sub1_matches} matches), Sub2: {sub2_ep_pattern} ({sub2_matches} matches)")
    
    return {
        "sub1_ep_pattern": sub1_ep_pattern,
        "sub2_ep_pattern": sub2_ep_pattern
    }

def verify_patterns(files, patterns, japanese_files, logger):
    """
    Verify the suggested patterns and return metrics.
    """
    sub1_pattern = patterns.get('sub1_pattern', '')
    sub2_pattern = patterns.get('sub2_pattern', '')
    sub1_ep_pattern = patterns.get('sub1_ep_pattern', '')
    sub2_ep_pattern = patterns.get('sub2_ep_pattern', '')
    
    # Count matches for each pattern
    sub1_matches = [f for f in files if re.search(sub1_pattern, f.name, re.IGNORECASE)]
    sub2_matches = [f for f in files if re.search(sub2_pattern, f.name, re.IGNORECASE)]
    
    # Count overlap (files matching both patterns)
    overlap = [f for f in sub1_matches if f in sub2_matches]
    
    # Count episode pattern matches
    sub1_ep_matches = [f for f in sub1_matches if re.search(sub1_ep_pattern, f.name, re.IGNORECASE)]
    sub2_ep_matches = [f for f in sub2_matches if re.search(sub2_ep_pattern, f.name, re.IGNORECASE)]
    
    return {
        "sub1_matches": len(sub1_matches),
        "sub2_matches": len(sub2_matches),
        "overlap": len(overlap),
        "sub1_ep_matches": len(sub1_ep_matches),
        "sub2_ep_matches": len(sub2_ep_matches)
    }

def detect_conflicts(files, patterns, logger):
    """
    Detect files that match multiple patterns for the same episode number.
    
    Args:
        files: List of Path objects for subtitle files
        patterns: Dictionary of patterns to check
        logger: Logger instance
        
    Returns:
        dict: Dictionary of conflicts by episode and language
    """
    conflicts = {}
    
    # Known episode number formats
    episode_formats = [
        (r'[Ss](\d+)[Ee](\d+)', "SxxExx format (e.g. S01E05)"),
        (r'[Ee]p(?:isode)?[\s._-]*(\d+)', "Episode format (e.g. ep05)"),
        (r'[\s._-](\d{2,3})(?:[\s._-]|$)', "Simple number format (e.g. _05_)"),
        (r'(?:^|\s|_|-)\[?(\d{2,3})\]?(?:\s|$|\.)', "Bracketed number format (e.g. [05])")
    ]
    
    try:
        # Group files by episode number
        episode_files = {}
        
        for file in files:
            # Try to extract episode number using each format
            for pattern, desc in episode_formats:
                match = re.search(pattern, file.name)
                if match:
                    # Get the episode number (use last group if multiple)
                    ep_num = match.group(match.lastindex)
                    ep_num = str(int(ep_num))  # Normalize (e.g. "05" -> "5")
                    
                    # Determine language (Japanese or English)
                    is_japanese, _ = check_for_japanese(file, logger)
                    lang = "Japanese" if is_japanese else "English"
                    
                    # Create key for this episode and language
                    key = (ep_num, lang)
                    if key not in episode_files:
                        episode_files[key] = []
                    episode_files[key].append(file)
                    break
        
        # Check for conflicts
        for (ep_num, lang), files in episode_files.items():
            if len(files) > 1:
                # Group files by their patterns
                pattern_groups = {}
                
                for file in files:
                    # Find which pattern(s) this file matches
                    for pattern, desc in episode_formats:
                        if re.search(pattern, file.name):
                            if pattern not in pattern_groups:
                                pattern_groups[pattern] = {
                                    'pattern': pattern,
                                    'description': desc,
                                    'matches': [],
                                    'examples': []
                                }
                            pattern_groups[pattern]['matches'].append(str(file))
                            # Add an example if we don't have one yet
                            if not pattern_groups[pattern]['examples']:
                                pattern_groups[pattern]['examples'].append(str(file))
                
                # If we found multiple patterns, record the conflict
                if len(pattern_groups) > 1:
                    conflicts[(ep_num, lang)] = {
                        'episode': ep_num,
                        'language': lang,
                        'patterns': list(pattern_groups.values())
                    }
                    
        logger.debug(f"Found {len(conflicts)} pattern conflicts")
        return conflicts
        
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}")
        return {}  # Return empty dict on error 