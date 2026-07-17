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
        "white": WHITE,
        "yellow": YELLOW,
        "red": RED,
        "blue": BLUE,
        "green": GREEN,
        "default": YELLOW,
    }

    color_lower = color.lower()
    if color_lower in color_map:
        return color_map[color_lower]
    elif color.startswith("#") and len(color) == 7:
        # Validate hex color
        if re.match(r"^#[0-9A-Fa-f]{6}$", color):
            return color
        else:
            raise ValueError(f"Invalid hex color format: {color}")
    else:
        raise ValueError(
            f"Invalid color: {color}. Use white, yellow, red, blue, green, or #RRGGBB format."
        )


def detect_episode_pattern(filenames: list, sample_size: int = 10) -> str:
    """
    Intelligently detect episode number pattern from a list of filenames.
    Returns a regex pattern with a capture group for the episode number.
    """
    import re
    from collections import Counter

    # Common episode patterns to test
    test_patterns = [
        (r"[Ss](\d+)[Ee](\d+)", "SxxExx"),  # S01E01, s1e2
        (r"[Ee]p\.?\s*(\d+)", "Ep"),  # Ep 01, EP02
        (r"[Ee]pisode\s*(\d+)", "Episode"),  # Episode 01
        (r"[Ee](\d{2,3})", "E##"),  # E01, E123
        (r"(\d{1,2})\s*[vV]\d", "#v#"),  # 01 v1
        (r"(\d{1,3})\s*(?:END|ENDING)", "#END"),  # 12 END
        (r"(\d{1,3})\s*(?:OP|OPENING)", "#OP"),  # 01 OP
        (r"(\d{1,3})\s*(?:ED|ENDING)", "#ED"),  # 02 ED
        (r"\((\d{1,3})\)", "(#)"),  # (01)
        (r"\[(\d{1,3})\]", "[#]"),  # [01]
        (r"(?:^|[^0-9])(\d{1,3})(?:[^0-9]|$)", "generic"),  # standalone numbers
    ]

    # Limit sample size for performance
    test_files = filenames[:sample_size]

    # Score each pattern based on how many files it matches consistently
    pattern_scores = {}

    for pattern_regex, pattern_name in test_patterns:
        matches = []
        for fname in test_files:
            m = re.search(pattern_regex, fname)
            if m:
                # For SxxExx, use episode number (group 2)
                if pattern_name == "SxxExx" and len(m.groups()) >= 2:
                    matches.append(m.group(2))
                elif m.groups():
                    matches.append(m.group(1))

        if len(matches) >= max(
            2, len(test_files) * 0.5
        ):  # Match at least 50% or 2 files
            # Check if episodes are sequential/unique (good sign)
            try:
                eps = [int(e) for e in matches]
                unique_eps = len(set(eps))
                if unique_eps == len(eps):  # All unique
                    pattern_scores[pattern_regex] = len(matches) * 10 + unique_eps
                else:
                    pattern_scores[pattern_regex] = len(matches) * 5
            except ValueError:
                pattern_scores[pattern_regex] = len(matches)

    if pattern_scores:
        best_pattern = max(pattern_scores, key=pattern_scores.get)
        return best_pattern

    # Fallback: generic number pattern
    return r"(\d+)"


def _analyze_filename_patterns(filenames: list) -> dict:
    """
    Analyze subtitle filenames to detect common patterns for track identification.
    Returns dict with suggested sub1_pattern, sub2_pattern, and track info.
    """
    import re
    from collections import Counter

    names = [f.name if hasattr(f, "name") else str(f) for f in filenames]

    # Common language/release group patterns in filenames
    track_indicators = {
        "language": [
            (r"\.(eng|english)\.", "eng"),
            (r"\.(jpn|japanese)\.", "jpn"),
            (r"\.(chi|chinese|zh)\.", "chi"),
            (r"\.(kor|korean)\.", "kor"),
            (r"\.(spa|spanish)\.", "spa"),
            (r"\.(fre|french)\.", "fre"),
            (r"\.(ger|german)\.", "ger"),
            (r"\.(ita|italian)\.", "ita"),
            (r"\.(por|portuguese)\.", "por"),
            (r"\.(rus|russian)\.", "rus"),
            (r"\.(ara|arabic)\.", "ara"),
            (r"\.(heb|hebrew)\.", "heb"),
            (r"\.(tha|thai)\.", "tha"),
            (r"\.(vie|vietnamese)\.", "vie"),
            (r"\.(ind|indonesian)\.", "ind"),
            (r"\.(tur|turkish)\.", "tur"),
            (r"\.(pol|polish)\.", "pol"),
            (r"\.(dut|dutch)\.", "dut"),
            (r"\.(swe|swedish)\.", "swe"),
            (r"\.(nor|norwegian)\.", "nor"),
            (r"\.(dan|danish)\.", "dan"),
            (r"\.(fin|finnish)\.", "fin"),
            (r"\.(ces|czech)\.", "ces"),
            (r"\.(hun|hungarian)\.", "hun"),
            (r"\.(ron|romanian)\.", "ron"),
            (r"\.(bul|bulgarian)\.", "bul"),
            (r"\.(hrv|croatian)\.", "hrv"),
            (r"\.(slk|slovak)\.", "slk"),
            (r"\.(slv|slovenian)\.", "slv"),
            (r"\.(est|estonian)\.", "est"),
            (r"\.(lav|latvian)\.", "lav"),
            (r"\.(lit|lithuanian)\.", "lit"),
            (r"\.(ukr|ukrainian)\.", "ukr"),
            (r"\.(cat|catalan)\.", "cat"),
            (r"\.(eus|basque)\.", "eus"),
            (r"\.(glg|galician)\.", "glg"),
            # Language at end before extension
            (
                r"\.(eng|jpn|chi|kor|spa|fre|ger|ita|por|rus|ara|heb|tha|vie|ind|tur|pol|dut|swe|nor|dan|fin|ces|hun|ron|bul|hrv|slk|slv|est|lav|lit|ukr|cat|eus|glg)\.srt$",
                "lang_suffix",
            ),
            # Bracketed language
            (
                r"\[(eng|jpn|chi|kor|spa|fre|ger|ita|por|rus|ara|heb|tha|vie|ind|tur|pol|dut|swe|nor|dan|fin|ces|hun|ron|bul|hrv|slk|slv|est|lav|lit|ukr|cat|eus|glg)\]",
                "lang_bracket",
            ),
            # Parenthetical language
            (
                r"\((eng|jpn|chi|kor|spa|fre|ger|ita|por|rus|ara|heb|tha|vie|ind|tur|pol|dut|swe|nor|dan|fin|ces|hun|ron|bul|hrv|slk|slv|est|lav|lit|ukr|cat|eus|glg)\)",
                "lang_paren",
            ),
        ],
        "release_group": [
            (r"\[([A-Za-z0-9\-]+)\]", "bracket"),
            (r"\(([A-Za-z0-9\-]+)\)", "paren"),
            (r"^-([A-Za-z0-9\-]+)-", "dash_prefix"),
            (r"-([A-Za-z0-9\-]+)\.srt$", "dash_suffix"),
        ],
        "format": [
            (r"\.(srt|ass|ssa|vtt|sub|idx)\.srt$", "double_ext"),
            (r"\.(bdrip|webrip|hdtv|web|blu?ray|dvdrip)\.", "source"),
            (r"\.(hevc|h264|h265|x264|x265|av1)\.", "codec"),
            (r"\.(1080p|720p|2160p|4k)\.", "resolution"),
        ],
        "track_type": [
            (r"\.(forced|signs|songs|commentary|full|sdh|cc)\.", "track_type"),
            (r"\[(forced|signs|songs|commentary|full|sdh|cc)\]", "track_type_bracket"),
        ],
    }

    # Count occurrences of each indicator type
    detected = {
        "languages": Counter(),
        "release_groups": Counter(),
        "formats": Counter(),
        "track_types": Counter(),
    }

    for name in names:
        for category, patterns in track_indicators.items():
            for pattern, ptype in patterns:
                matches = re.findall(pattern, name, re.IGNORECASE)
                if matches:
                    if category == "language":
                        detected["languages"].update(matches)
                    elif category == "release_group":
                        detected["release_groups"].update(matches)
                    elif category == "format":
                        detected["formats"].update(matches)
                    elif category == "track_type":
                        detected["track_types"].update(matches)

    return detected


def _auto_detect_subtitle_tracks(filenames: list, max_tracks: int = 2) -> list:
    """
    Automatically detect distinct subtitle tracks from a list of filenames.
    Returns list of dicts with pattern and description for each track.
    """
    import re
    from collections import Counter

    detected = _analyze_filename_patterns(filenames)

    tracks = []

    # Prioritize language detection
    if detected["languages"]:
        # Get most common languages
        for lang, count in detected["languages"].most_common(max_tracks):
            # Create pattern to match this language
            pattern = rf"\.{re.escape(lang)}\."
            tracks.append(
                {
                    "pattern": pattern,
                    "description": f"Language: {lang.upper()}",
                    "type": "language",
                    "value": lang,
                    "count": count,
                }
            )

    # If not enough language tracks, try track types
    if len(tracks) < max_tracks and detected["track_types"]:
        for ttype, count in detected["track_types"].most_common(
            max_tracks - len(tracks)
        ):
            pattern = rf"\.{re.escape(ttype)}\."
            tracks.append(
                {
                    "pattern": pattern,
                    "description": f"Track type: {ttype}",
                    "type": "track_type",
                    "value": ttype,
                    "count": count,
                }
            )

    # If still not enough, try release groups
    if len(tracks) < max_tracks and detected["release_groups"]:
        for group, count in detected["release_groups"].most_common(
            max_tracks - len(tracks)
        ):
            pattern = rf"\[{re.escape(group)}\]"
            tracks.append(
                {
                    "pattern": pattern,
                    "description": f"Release group: {group}",
                    "type": "release_group",
                    "value": group,
                    "count": count,
                }
            )

    # Fallback: split by any distinguishing pattern
    if len(tracks) < 2:
        # Find words that appear in some but not all filenames
        all_words = []
        for name in filenames:
            # Extract words (alphanumeric sequences)
            words = re.findall(r"\b[A-Za-z]{2,}\b", name)
            all_words.extend(words)

        word_counts = Counter(all_words)
        total = len(filenames)

        # Words that appear in 10-90% of files (distinguishing)
        distinguishing = [
            (w, c) for w, c in word_counts.most_common(10) if 0.1 <= c / total <= 0.9
        ]

        for word, count in distinguishing[: max_tracks - len(tracks)]:
            pattern = rf"\b{re.escape(word)}\b"
            tracks.append(
                {
                    "pattern": pattern,
                    "description": f"Distinguishing word: {word}",
                    "type": "word",
                    "value": word,
                    "count": count,
                }
            )

    return tracks[:max_tracks]


def _detect_language_from_content(filepath: str) -> str:
    """
    Detect language from subtitle file content.
    Returns ISO 639-2 language code or empty string.
    """
    try:
        import re
        from pathlib import Path

        # Read first portion of file
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")[:5000]

        # Common language indicators in subtitle content
        lang_patterns = {
            "jpn": [
                r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]",
                r"です|ます|だ|だね|だよ|なの|なのだ|なのです",
            ],
            "kor": [r"[\uAC00-\uD7AF]", r"입니다|입니다만|해요|합니다|이다|이다만"],
            "chi": [
                r"[\u4E00-\u9FFF]",
                r"的|了|是|在|有|和|我|你|他|她|这|那|不|要|去|来|好|坏",
            ],
            "eng": [
                r"\b(the|and|you|that|for|with|this|are|was|his|her|has|had|but|not|what|when|where|who|why|how)\b"
            ],
            "spa": [
                r"\b(el|la|los|las|un|una|y|de|en|que|es|por|con|no|se|su|al|lo|como|más|pero|sus|le|me|mi|te|ti|tu)\b"
            ],
            "fre": [
                r"\b(le|la|les|un|une|et|de|en|que|est|pour|avec|ne|se|son|sa|au|du|des|comme|plus|mais|ses|leur|lui|moi|toi|tu)\b"
            ],
            "ger": [
                r"\b(der|die|das|ein|eine|und|den|dem|des|von|zu|ist|mit|sich|auf|für|als|auch|im|am|an|ab|aus|bei|ein|er|es|ich|du|wir|ihr|sie)\b"
            ],
            "ita": [
                r"\b(il|la|lo|gli|le|un|uno|una|e|di|in|che|è|per|con|non|si|su|sul|sui|alle|ai|dal|dei|dai|dagli|dagli)\b"
            ],
            "por": [
                r"\b(o|a|os|as|um|uma|e|de|em|que|é|por|com|não|se|seu|sua|ao|do|da|dos|das|no|na|nos|nas|pelo|pela|pelos|pelas)\b"
            ],
            "rus": [
                r"[\u0400-\u04FF]",
                r"и|в|не|на|я|что|то|он|а|как|это|по|этот|к|но|да|ты|мы|с|у|из|о|же|за|ли|бы|очень|быть|как|если|или|так|тоже|только|уж|уже|именно|именно|именно",
            ],
        }

        scores = {}
        for lang, patterns in lang_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores, key=scores.get)

        return ""
    except Exception:
        return ""


def _group_files_by_language(files: list) -> dict:
    """
    Group subtitle files by detected language.
    Returns dict: {language: [files...]}
    """
    from collections import defaultdict
    import re

    groups = defaultdict(list)
    for f in files:
        lang = _detect_language_from_content(str(f))
        if not lang:
            # Try to extract from filename
            name = f.name if hasattr(f, "name") else str(f)
            match = re.search(r"\.([a-z]{3})\.", name, re.IGNORECASE)
            if match:
                lang = match.group(1).lower()
        if not lang:
            lang = "unknown"
        groups[lang].append(f)
    return dict(groups)


def _extract_episode_number(filename: str) -> str:
    """Extract episode number from filename."""
    import re

    # Try SxxExx first
    sxxexx = re.search(r"[Ss](\d+)[Ee](\d+)", filename)
    if sxxexx:
        return sxxexx.group(2)
    # Try E##
    e_match = re.search(r"[Ee](\d{2,3})", filename)
    if e_match:
        return e_match.group(1)
    # Try standalone number at end or before extension
    num_match = re.search(r"[^0-9](\d{1,3})(?:[^0-9]|$)", filename)
    if num_match:
        return num_match.group(1)
    return "00"


def _select_main_track_per_episode(files: list) -> list:
    """
    From files, group by (language, episode) and select main dialogue track per episode.
    Prefers file with most content (full dialogue vs signs/songs).
    """
    from collections import defaultdict
    from pathlib import Path
    import re

    # Group by (language, episode)
    groups = defaultdict(list)
    for f in files:
        lang = _detect_language_from_content(str(f))
        if not lang:
            name = f.name if hasattr(f, "name") else str(f)
            match = re.search(r"\.([a-z]{3})\.", name, re.IGNORECASE)
            if match:
                lang = match.group(1).lower()
        if not lang:
            lang = "unknown"
        ep = _extract_episode_number(f.name if hasattr(f, "name") else str(f))
        groups[(lang, ep)].append(f)

    selected = []
    for (lang, ep), ep_files in groups.items():
        if len(ep_files) == 1:
            selected.append(ep_files[0])
            print(f"  Selected {lang} E{ep}: {ep_files[0].name}")
        else:
            # Score by content size
            best_file = None
            best_score = -1
            for f in ep_files:
                try:
                    content = Path(str(f)).read_text(encoding="utf-8", errors="ignore")
                    score = len(content) + content.count("\n") * 100
                    if score > best_score:
                        best_score = score
                        best_file = f
                except Exception:
                    continue
            if best_file:
                selected.append(best_file)
                print(
                    f"  Selected main {lang} E{ep}: {best_file.name} ({best_score} chars)"
                )
            else:
                selected.append(ep_files[0])
    return selected


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
    convert_to_ass: bool = False,
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
            output_encoding=codec,
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
            preserve_svg=preserve_svg,
        )

        # Add second subtitle
        merger.add(
            sub2_path,
            codec=codec,
            color=WHITE,  # Second subtitle is always white
            size=sub2_size,
            time_offset=sub2_delay,
            bold=sub2_bold,
            preserve_svg=preserve_svg,
        )

        # Perform merge
        merger.merge()
        print(f"Successfully merged subtitles to: {output_path}")

        # Convert to ASS if requested
        if convert_to_ass:
            from src.utils.ass_converter import create_ass_from_srt

            ass_path = str(Path(output_path).with_suffix(".ass"))

            style_kwargs = {
                "font": "MS Gothic",  # Japanese font
                "font_size": sub1_size,
                "ruby_font_size": sub1_size // 2,  # Half the size for ruby
                "text_color": normalized_color,
                "outline_size": 1.5,  # Thinner outline
                "shadow_size": 0.5,  # Subtle shadow
                "auto_generate_furigana": True,  # Use automatic furigana generation
                "advanced_styling": True,  # Use advanced styling with separate dialogue entries
            }

            ass_file = create_ass_from_srt(
                srt_file_path=output_path, output_dir=str(output_dir), **style_kwargs
            )

        print(f"Converted to ASS format: {ass_file}")

        return True

    except Exception as e:
        print(f"Error during merge operation: {e}")
        import traceback

        traceback.print_exc()
        return False


def _detect_episode_pattern(filenames) -> str:
    """
    Intelligently detect episode number pattern from a list of filenames.
    Returns a regex pattern with a capture group for the episode number.
    """
    from pathlib import Path
    import re
    from collections import Counter

    # Get just filenames if Path objects
    names = [f.name if isinstance(f, Path) else str(f) for f in filenames]

    # Common episode patterns to test
    test_patterns = [
        (r"[Ss](\d+)[Ee](\d+)", "SxxExx"),  # S01E01, s1e2
        (r"[Ee]p\.?\s*(\d+)", "Ep"),  # Ep 01, EP02
        (r"[Ee]pisode\s*(\d+)", "Episode"),  # Episode 01
        (r"[Ee](\d{2,3})", "E##"),  # E01, E123
        (r"(\d{1,2})\s*[vV]\d", "#v#"),  # 01 v1
        (r"(\d{1,3})\s*(?:END|ENDING)", "#END"),  # 12 END
        (r"(\d{1,3})\s*(?:OP|OPENING)", "#OP"),  # 01 OP
        (r"(\d{1,3})\s*(?:ED|ENDING)", "#ED"),  # 02 ED
        (r"\((\d{1,3})\)", "(#)"),  # (01)
        (r"\[(\d{1,3})\]", "[#]"),  # [01]
        (r"(?:^|[^0-9])(\d{1,3})(?:[^0-9]|$)", "generic"),  # standalone numbers
    ]

    # Limit sample size for performance
    test_files = names[:20]

    # Score each pattern based on how many files it matches consistently
    pattern_scores = {}

    for pattern_regex, pattern_name in test_patterns:
        matches = []
        for fname in test_files:
            m = re.search(pattern_regex, fname)
            if m:
                # For SxxExx, use episode number (group 2)
                if pattern_name == "SxxExx" and len(m.groups()) >= 2:
                    matches.append(m.group(2))
                elif m.groups():
                    matches.append(m.group(1))

        if len(matches) >= max(
            2, len(test_files) * 0.5
        ):  # Match at least 50% or 2 files
            # Check if episodes are sequential/unique (good sign)
            try:
                eps = [int(e) for e in matches]
                unique_eps = len(set(eps))
                if unique_eps == len(eps):  # All unique
                    pattern_scores[pattern_regex] = len(matches) * 10 + unique_eps
                else:
                    pattern_scores[pattern_regex] = len(matches) * 5
            except ValueError:
                pattern_scores[pattern_regex] = len(matches)

    if pattern_scores:
        best_pattern = max(pattern_scores, key=pattern_scores.get)
        return best_pattern

    # Fallback: generic number pattern
    return r"(\d+)"


def batch_merge_directory(
    input_dir: str,
    video_dir: str,
    output_dir: Optional[str] = None,
    sub1_pattern: str = r".*\.srt$",
    sub2_pattern: str = r".*\.srt$",
    sub1_episode_pattern: str = r"(\d+)",
    sub2_episode_pattern: str = r"(\d+)",
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
    color: str = "yellow",
    auto_detect_episodes: bool = True,
    auto_detect_tracks: bool = False,
    detect_language_content: bool = False,
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
        auto_detect_episodes: Auto-detect episode number patterns
        auto_detect_tracks: Auto-detect subtitle tracks from filename patterns
        detect_language_content: Detect subtitle language from file content
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
        all_srt_files = list(input_path.glob("*.srt"))
        print(f"Found {len(all_srt_files)} total .srt files")

        # Find matching files using patterns
        sub1_files = [
            f for f in all_srt_files if re.search(sub1_pattern, f.name, re.IGNORECASE)
        ]
        sub2_files = [
            f for f in all_srt_files if re.search(sub2_pattern, f.name, re.IGNORECASE)
        ]

        print(f"Found {len(sub1_files)} sub1 files and {len(sub2_files)} sub2 files")

        # Auto-detect subtitle track patterns if using defaults (both are .*\.srt$)
        if (
            auto_detect_episodes
            and sub1_pattern == r".*\.srt$"
            and sub2_pattern == r".*\.srt$"
        ):
            print("Auto-detecting subtitle track patterns...")
            all_matched_files = sub1_files + sub2_files
            tracks = _auto_detect_subtitle_tracks(all_matched_files, max_tracks=2)

            if len(tracks) >= 2:
                sub1_pattern = tracks[0]["pattern"]
                sub2_pattern = tracks[1]["pattern"]
                print(
                    f"  Auto-detected sub1 pattern: {sub1_pattern} ({tracks[0]['description']})"
                )
                print(
                    f"  Auto-detected sub2 pattern: {sub2_pattern} ({tracks[1]['description']})"
                )

                # Re-filter files with detected patterns
                sub1_files = [
                    f
                    for f in all_matched_files
                    if re.search(sub1_pattern, f.name, re.IGNORECASE)
                ]
                sub2_files = [
                    f
                    for f in all_matched_files
                    if re.search(sub2_pattern, f.name, re.IGNORECASE)
                ]
                print(
                    f"  Re-filtered: {len(sub1_files)} sub1 files, {len(sub2_files)} sub2 files"
                )
            elif len(tracks) == 1:
                print(f"  Only one track type detected: {tracks[0]['description']}")
                print("  Falling back to manual pattern specification")

        # Auto-detect language from content if enabled
        if detect_language_content and len(sub1_files) > 0 and len(sub2_files) > 0:
            print("Detecting subtitle languages from content...")
            # Sample a few files from each track
            sample_size = min(3, len(sub1_files), len(sub2_files))
            sub1_langs = []
            sub2_langs = []

            for i in range(sample_size):
                lang1 = _detect_language_from_content(str(sub1_files[i]))
                lang2 = _detect_language_from_content(str(sub2_files[i]))
                if lang1:
                    sub1_langs.append(lang1)
                if lang2:
                    sub2_langs.append(lang2)

            # Get most common language for each track
            from collections import Counter

            if sub1_langs:
                sub1_lang = Counter(sub1_langs).most_common(1)[0][0]
                print(f"  Detected sub1 language: {sub1_lang}")
            if sub2_langs:
                sub2_lang = Counter(sub2_langs).most_common(1)[0][0]
                print(f"  Detected sub2 language: {sub2_lang}")

        # If multiple files per language, select the one with most content (full dialogue vs signs/songs)
        if auto_detect_tracks:
            print("Selecting main dialogue track per episode...")

            # Filter out already-merged files
            def is_merged(f):
                name = f.name if hasattr(f, "name") else str(f)
                return "_merged" in name

            sub1_original = [f for f in sub1_files if not is_merged(f)]
            sub2_original = [f for f in sub2_files if not is_merged(f)]

            # Group by language and episode, select main track per episode
            sub1_files = _select_main_track_per_episode(sub1_original)
            sub2_files = _select_main_track_per_episode(sub2_original)
            print(
                f"  Selected {len(sub1_files)} sub1 track(s), {len(sub2_files)} sub2 track(s)"
            )

        # Auto-detect episode patterns if using defaults
        if auto_detect_episodes:
            if sub1_episode_pattern == r"(\d+)":
                sub1_episode_pattern = _detect_episode_pattern(sub1_files)
                print(f"Auto-detected sub1 episode pattern: {sub1_episode_pattern}")
            if sub2_episode_pattern == r"(\d+)":
                sub2_episode_pattern = _detect_episode_pattern(sub2_files)
                print(f"Auto-detected sub2 episode pattern: {sub2_episode_pattern}")

        # Create episode pairs dictionary
        episode_subs = {}

        # Process sub1 files
        for sub1 in sub1_files:
            try:
                # Try SxxExx pattern first
                sxxexx_match = re.search(r"[Ss](\d+)[Ee](\d+)", sub1.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                else:
                    # Try configured pattern
                    match = re.search(sub1_episode_pattern, sub1.stem)
                    if match:
                        ep_num = match.group(1)
                        season_num = "01"  # Default season
                    else:
                        # Try extracting episode number from filename
                        ep_match = re.search(
                            r"(?:^|\s|_|-|\[)(\d{1,2})(?:\s|$|\]|\[|\()", sub1.stem
                        )
                        if ep_match:
                            ep_num = ep_match.group(1)
                            season_num = "01"  # Default season
                        else:
                            print(
                                f"Could not extract episode info from sub1 file: {sub1.name}"
                            )
                            continue

                # Create a unique key combining season and episode
                ep_key = f"S{season_num}E{ep_num}"

                if ep_key not in episode_subs:
                    episode_subs[ep_key] = {
                        "sub1": sub1,
                        "season": season_num,
                        "episode": ep_num,
                        "file_name": sub1.name,
                    }
                    print(f"Found sub1 for {ep_key}: {sub1.name}")

            except Exception as e:
                print(f"Error processing sub1 file {sub1}: {e}")

        # Process sub2 files
        for sub2 in sub2_files:
            try:
                # Try SxxExx pattern first
                sxxexx_match = re.search(r"[Ss](\d+)[Ee](\d+)", sub2.stem)
                if sxxexx_match:
                    season_num = sxxexx_match.group(1)
                    ep_num = sxxexx_match.group(2)
                else:
                    # Try configured pattern
                    match = re.search(sub2_episode_pattern, sub2.stem)
                    if match:
                        ep_num = match.group(1)
                        season_num = "01"  # Default season
                    else:
                        # Try extracting episode number from filename
                        ep_match = re.search(
                            r"(?:^|\s|_|-|\[)(\d{1,2})(?:\s|$|\]|\[|\()", sub2.stem
                        )
                        if ep_match:
                            ep_num = ep_match.group(1)
                            season_num = "01"  # Default season
                        else:
                            print(
                                f"Could not extract episode info from sub2 file: {sub2.name}"
                            )
                            continue

                # Create a unique key combining season and episode
                ep_key = f"S{season_num}E{ep_num}"

                if ep_key in episode_subs:
                    episode_subs[ep_key]["sub2"] = sub2
                    print(f"Found sub2 for {ep_key}: {sub2.name}")
                else:
                    print(f"Found unmatched sub2 for {ep_key}: {sub2.name}")

            except Exception as e:
                print(f"Error processing sub2 file {sub2}: {e}")

        # Display summary of matched subtitles
        matched_pairs = [
            k for k, v in episode_subs.items() if "sub1" in v and "sub2" in v
        ]
        print(f"Found {len(matched_pairs)} matched subtitle pairs")

        # Process matched pairs
        success_count = 0
        for pair in matched_pairs:
            sub1_file = episode_subs[pair]["sub1"]
            sub2_file = episode_subs[pair]["sub2"]

            # Find corresponding video file (for output naming and ALASS sync)
            video_file = None
            video_extensions = [
                ".mp4",
                ".mkv",
                ".avi",
                ".mov",
                ".wmv",
                ".flv",
                ".webm",
                ".m4v",
            ]
            for ext in video_extensions:
                potential_video = video_path / f"{sub1_file.stem}{ext}"
                if potential_video.exists():
                    video_file = potential_video
                    break

            # Also try with episode number patterns
            if not video_file:
                for video_file_in_dir in video_path.glob("*"):
                    if video_file_in_dir.suffix.lower() in video_extensions:
                        # Check SxxExx pattern (allow optional whitespace)
                        sxxexx_match = re.search(
                            r"[Ss](\d+)\s*[Ee](\d+)", video_file_in_dir.stem
                        )
                        if sxxexx_match:
                            ep_num = sxxexx_match.group(2)
                            if ep_num == episode_subs[pair]["episode"]:
                                video_file = video_file_in_dir
                                break

            # Generate output filename based on video file if available, otherwise sub1
            if video_file:
                output_name = f"{video_file.stem}.merged.srt"
                # Output to video directory when video file found
                output_file = video_path / output_name
            else:
                output_name = f"{sub1_file.stem}_merged.srt"
                output_file = output_path / output_name

            print(
                f"Merging {sub1_file.name} and {sub2_file.name} -> {output_file.name}"
            )

            # Prepare for ALASS sync if enabled
            temp_sub1_path = str(sub1_file)
            temp_sub2_path = str(sub2_file)

            if enable_alass_sync and video_file:
                try:
                    # Sync first subtitle with ALASS
                    temp_sub1_path = sync_subtitle_with_alass(
                        str(video_file),
                        str(sub1_file),
                        alass_path,
                        alass_interval,
                        alass_split_penalty,
                        alass_sub_fps,
                        alass_ref_fps,
                        disable_fps_guessing,
                    )

                    # Sync second subtitle with ALASS
                    temp_sub2_path = sync_subtitle_with_alass(
                        str(video_file),
                        str(sub2_file),
                        alass_path,
                        alass_interval,
                        alass_split_penalty,
                        alass_sub_fps,
                        alass_ref_fps,
                        disable_fps_guessing,
                    )

                    print(f"  ALASS sync completed for both subtitles")
                except Exception as e:
                    print(f"  Warning: ALASS sync failed, using original files: {e}")

            # Create merger instance
            merger = Merger(
                output_path=str(output_file.parent),
                output_name=output_file.name,
                output_encoding=codec,
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
                preserve_svg=preserve_svg,
            )

            # Add second subtitle
            merger.add(
                temp_sub2_path,
                codec=codec,
                color=WHITE,  # Second subtitle is always white
                size=sub2_size,
                time_offset=sub2_delay,
                bold=sub2_bold,
                preserve_svg=preserve_svg,
            )

            # Perform merge
            merger.merge()
            print(f"  Merged: {output_file.name}")
            success_count += 1

            # Convert to ASS if requested
            if convert_to_ass:
                from src.utils.ass_converter import create_ass_from_srt

                ass_path = str(output_file.with_suffix(".ass"))

                style_kwargs = {
                    "font": "MS Gothic",  # Japanese font
                    "font_size": sub1_size,
                    "ruby_font_size": sub1_size // 2,  # Half the size for ruby
                    "text_color": normalized_color,
                    "outline_size": 1.5,  # Thinner outline
                    "shadow_size": 0.5,  # Subtle shadow
                    "auto_generate_furigana": True,  # Use automatic furigana generation
                    "advanced_styling": True,  # Use advanced styling with separate dialogue entries
                }

                ass_file = create_ass_from_srt(
                    srt_file_path=str(output_file),
                    output_dir=str(output_path),
                    **style_kwargs,
                )

                print(f"  Converted to ASS: {Path(ass_file).name}")

        print(
            f"\nBatch processing completed. Successfully processed {success_count} pairs."
        )
        return True

    except Exception as e:
        print(f"Error during batch merge operation: {e}")
        import traceback

        traceback.print_exc()
        return False


def sync_subtitle_with_alass(
    video_path: str,
    subtitle_path: str,
    alass_path: str = "",
    alass_interval: int = 100,
    alass_split_penalty: float = 10.0,
    alass_sub_fps: float = 23.976,
    alass_ref_fps: float = 23.976,
    disable_fps_guessing: bool = False,
) -> str:
    """Synchronize subtitle with ALASS using the video as reference."""
    import subprocess
    import os
    from pathlib import Path

    # Determine ALASS path
    if not alass_path:
        # Try to find alass in system PATH
        import shutil

        alass_path = shutil.which("alass")
        if not alass_path:
            # Default fallback path
            alass_path = "/usr/bin/alass"

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
            "--interval",
            str(alass_interval),
            "--split-penalty",
            str(alass_split_penalty),
            "--sub-fps-inc",
            str(alass_sub_fps),
            "--sub-fps-ref",
            str(alass_ref_fps),
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
        """,
    )

    subparsers = parser.add_subparsers(
        dest="mode", help="Operation mode", required=True
    )

    # Single file merge parser
    single_parser = subparsers.add_parser(
        "single", help="Merge two individual subtitle files"
    )
    single_parser.add_argument("sub1", help="Path to first subtitle file")
    single_parser.add_argument("sub2", help="Path to second subtitle file")
    single_parser.add_argument("output", help="Path for output merged file")
    single_parser.add_argument(
        "--color",
        default="yellow",
        help="Color for first subtitle (white, yellow, red, blue, green, or #RRGGBB)",
    )
    single_parser.add_argument(
        "--codec", default="utf-8", help="Text encoding (default: utf-8)"
    )
    single_parser.add_argument(
        "--sub1-size",
        type=int,
        default=16,
        help="Font size for first subtitle (default: 16)",
    )
    single_parser.add_argument(
        "--sub2-size",
        type=int,
        default=16,
        help="Font size for second subtitle (default: 16)",
    )
    single_parser.add_argument(
        "--sub1-delay",
        type=int,
        default=0,
        help="Time delay for first subtitle in ms (default: 0)",
    )
    single_parser.add_argument(
        "--sub2-delay",
        type=int,
        default=0,
        help="Time delay for second subtitle in ms (default: 0)",
    )
    single_parser.add_argument(
        "--sub1-bold", action="store_true", help="Make first subtitle bold"
    )
    single_parser.add_argument(
        "--sub2-bold", action="store_true", help="Make second subtitle bold"
    )
    single_parser.add_argument(
        "--enable-svg-filtering", action="store_true", help="Enable SVG filtering"
    )
    single_parser.add_argument(
        "--remove-text-entries", action="store_true", help="Remove text entries"
    )
    single_parser.add_argument(
        "--preserve-svg",
        action="store_true",
        default=True,
        help="Preserve SVG paths (default: True)",
    )
    single_parser.add_argument(
        "--no-preserve-svg",
        action="store_false",
        dest="preserve_svg",
        help="Do not preserve SVG paths",
    )
    single_parser.add_argument(
        "--convert-to-ass",
        action="store_true",
        help="Convert output to ASS format with furigana",
    )

    # Directory batch processing parser
    batch_parser = subparsers.add_parser(
        "batch", help="Batch merge subtitle files in a directory"
    )
    batch_parser.add_argument("input_dir", help="Directory containing subtitle files")
    batch_parser.add_argument(
        "video_dir", help="Directory containing video files for ALASS sync"
    )
    batch_parser.add_argument(
        "--output-dir", help="Directory for output files (defaults to input directory)"
    )
    batch_parser.add_argument(
        "--sub1-pattern",
        default=r".*\.srt$",
        help="Regex pattern for first subtitle type (default: .*\\.srt$)",
    )
    batch_parser.add_argument(
        "--sub2-pattern",
        default=r".*\.srt$",
        help="Regex pattern for second subtitle type (default: .*\\.srt$)",
    )
    batch_parser.add_argument(
        "--sub1-episode-pattern",
        default=r"(\d+)",
        help="Regex pattern for episode numbers in sub1 (default: (\\d+))",
    )
    batch_parser.add_argument(
        "--sub2-episode-pattern",
        default=r"(\d+)",
        help="Regex pattern for episode numbers in sub2 (default: (\\d+))",
    )
    batch_parser.add_argument(
        "--no-auto-detect-episodes",
        action="store_true",
        help="Disable automatic episode pattern detection",
    )
    batch_parser.add_argument(
        "--auto-detect-tracks",
        action="store_true",
        help="Automatically detect subtitle tracks by filename patterns (language, release group, etc.)",
    )
    batch_parser.add_argument(
        "--detect-language-content",
        action="store_true",
        help="Detect subtitle language from file content (slower, more accurate)",
    )
    batch_parser.add_argument(
        "--sub1-delay",
        type=int,
        default=0,
        help="Time delay for first subtitle in ms (default: 0)",
    )
    batch_parser.add_argument(
        "--sub2-delay",
        type=int,
        default=0,
        help="Time delay for second subtitle in ms (default: 0)",
    )
    batch_parser.add_argument(
        "--codec", default="utf-8", help="Text encoding (default: utf-8)"
    )
    batch_parser.add_argument(
        "--enable-alass-sync", action="store_true", help="Enable ALASS auto-sync"
    )
    batch_parser.add_argument(
        "--alass-path", default="", help="Path to ALASS executable"
    )
    batch_parser.add_argument(
        "--alass-interval",
        type=int,
        default=100,
        help="ALASS interval parameter in ms (default: 100)",
    )
    batch_parser.add_argument(
        "--alass-split-penalty",
        type=float,
        default=10.0,
        help="ALASS split penalty parameter (default: 10.0)",
    )
    batch_parser.add_argument(
        "--alass-sub-fps",
        type=float,
        default=23.976,
        help="ALASS subtitle FPS (default: 23.976)",
    )
    batch_parser.add_argument(
        "--alass-ref-fps",
        type=float,
        default=23.976,
        help="ALASS reference FPS (default: 23.976)",
    )
    batch_parser.add_argument(
        "--disable-fps-guessing",
        action="store_true",
        help="Disable FPS guessing in ALASS",
    )
    batch_parser.add_argument(
        "--enable-svg-filtering", action="store_true", help="Enable SVG filtering"
    )
    batch_parser.add_argument(
        "--remove-text-entries", action="store_true", help="Remove text entries"
    )
    batch_parser.add_argument(
        "--preserve-svg",
        action="store_true",
        default=True,
        help="Preserve SVG paths (default: True)",
    )
    batch_parser.add_argument(
        "--no-preserve-svg",
        action="store_false",
        dest="preserve_svg",
        help="Do not preserve SVG paths",
    )
    batch_parser.add_argument(
        "--convert-to-ass",
        action="store_true",
        help="Convert output to ASS format with furigana",
    )
    batch_parser.add_argument(
        "--sub1-size",
        type=int,
        default=16,
        help="Font size for first subtitle (default: 16)",
    )
    batch_parser.add_argument(
        "--sub2-size",
        type=int,
        default=16,
        help="Font size for second subtitle (default: 16)",
    )
    batch_parser.add_argument(
        "--sub1-bold", action="store_true", help="Make first subtitle bold"
    )
    batch_parser.add_argument(
        "--sub2-bold", action="store_true", help="Make second subtitle bold"
    )
    batch_parser.add_argument(
        "--color",
        default="yellow",
        help="Color for first subtitle (white, yellow, red, blue, green, or #RRGGBB)",
    )

    args = parser.parse_args()

    if args.mode == "single":
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
            convert_to_ass=args.convert_to_ass,
        )
        sys.exit(0 if success else 1)

    elif args.mode == "batch":
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
            color=args.color,
            auto_detect_episodes=not args.no_auto_detect_episodes,
            auto_detect_tracks=args.auto_detect_tracks,
            detect_language_content=args.detect_language_content,
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
