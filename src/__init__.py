"""Subtitle Merger application package."""

from .components.style import COLORS, DARK_THEME
from .components.logger import setup_logger, QTextEditLogger
from .components.sync_controls import SyncControls
from .components.base_tab import BaseTab

from .utils.settings import Settings
from .utils.merger import MergeWorker
from .utils.file_utils import EpisodeMatch, find_subtitle_pairs, find_video_files

__version__ = '0.1.0' 