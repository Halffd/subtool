"""File operation utilities."""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class EpisodeMatch:
    """Data class for storing matched episode files."""
    episode_num: int
    sub1_path: Path
    sub2_path: Path
    output_path: Optional[Path] = None

def find_subtitle_pairs(
    directory: Path,
    sub1_pattern: str,
    sub2_pattern: str,
    sub1_ep_pattern: str,
    sub2_ep_pattern: str,
    logger=None
) -> Dict[str, Dict[str, Path]]:
    """Find matching subtitle pairs in directory."""
    episode_subs = {}
    
    try:
        # List all srt files
        all_srt_files = list(directory.glob('*.srt'))
        if logger:
            logger.debug(f"Found {len(all_srt_files)} total .srt files")
            for srt_file in all_srt_files:
                logger.debug(f"Found SRT file: {srt_file.name}")
        
        # Filter sub1 files
        sub1_files = [f for f in all_srt_files 
                     if re.search(sub1_pattern, f.name, re.IGNORECASE)]
        
        # Filter sub2 files
        sub2_files = [f for f in all_srt_files
                     if re.search(sub2_pattern, f.name, re.IGNORECASE)]
        
        if logger:
            logger.info(f"Found {len(sub1_files)} sub1 files and {len(sub2_files)} sub2 files")
        
        # Process sub1 files
        for sub1 in sub1_files:
            try:
                ep_match = re.search(sub1_ep_pattern, sub1.stem)
                if ep_match:
                    ep_num = ep_match.group(1)
                    if ep_num not in episode_subs:
                        episode_subs[ep_num] = {'sub1': sub1}
                        if logger:
                            logger.debug(f"Found sub1 for episode {ep_num}: {sub1.name}")
                    else:
                        if logger:
                            logger.warning(f"Duplicate sub1 for episode {ep_num}: {sub1.name}")
                else:
                    if logger:
                        logger.warning(f"Could not extract episode number from sub1 file: {sub1.name}")
            except Exception as e:
                if logger:
                    logger.error(f"Error processing sub1 file {sub1}: {e}")
        
        # Process sub2 files
        for sub2 in sub2_files:
            try:
                ep_match = re.search(sub2_ep_pattern, sub2.stem)
                if ep_match:
                    ep_num = ep_match.group(1)
                    if ep_num in episode_subs:
                        episode_subs[ep_num]['sub2'] = sub2
                        if logger:
                            logger.debug(f"Found sub2 for episode {ep_num}: {sub2.name}")
                    else:
                        if logger:
                            logger.warning(f"Found sub2 but no sub1 for episode {ep_num}: {sub2.name}")
                else:
                    if logger:
                        logger.warning(f"Could not extract episode number from sub2 file: {sub2.name}")
            except Exception as e:
                if logger:
                    logger.error(f"Error processing sub2 file {sub2}: {e}")
        
        return episode_subs
        
    except Exception as e:
        if logger:
            logger.error(f"Error finding subtitle pairs: {e}")
        return {}

def find_video_files(
    directory: Path,
    episode_pattern: str,
    logger=None
) -> List[Tuple[str, Path]]:
    """Find video files and extract episode numbers."""
    video_files = []
    
    try:
        # Find all mkv files
        mkv_files = list(directory.glob('**/*.mkv'))
        
        if logger:
            logger.info(f"Found {len(mkv_files)} video files")
        
        # Process each video file
        for video_file in mkv_files:
            if logger:
                logger.debug(f"Found video file: {video_file.name}")
            try:
                # Extract episode number
                match = re.search(episode_pattern, video_file.stem)
                if not match:
                    match = re.search(r'(\d+)', video_file.stem)
                    if not match:
                        if logger:
                            logger.warning(f"Could not find episode number in {video_file.name}")
                        continue
                
                ep_num = match.group(1)
                video_files.append((ep_num, video_file))
                if logger:
                    logger.debug(f"Extracted episode number {ep_num} from {video_file.name}")
                
            except Exception as e:
                if logger:
                    logger.error(f"Error processing video file {video_file}: {e}")
                continue
        
        return video_files
        
    except Exception as e:
        if logger:
            logger.error(f"Error finding video files: {e}")
        return [] 