"""Subtitle merger worker and utilities."""

from typing import List, Dict, Any
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from main import Merger

class MergeWorker(QThread):
    """Worker thread for handling subtitle merging operations."""
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, matches: List[Dict[str, Path]], merger_args: Dict[str, Any]):
        super().__init__()
        self.matches = matches
        self.merger_args = merger_args
        self.is_running = True

    def run(self):
        try:
            for match in self.matches:
                if not self.is_running:
                    break
                
                try:
                    self.progress.emit(f"Processing episode {match['episode_num']}")
                    
                    # Create merger instance
                    merger = Merger(output_name=str(match['output_path']))
                    
                    # Add subtitles
                    merger.add(
                        str(match['sub1_path']), 
                        color=self.merger_args['color'],
                        codec=self.merger_args['codec'],
                        size=self.merger_args.get('sub1_size', 16),
                        time_offset=self.merger_args.get('sub1_sync', 0)
                    )
                    merger.add(
                        str(match['sub2_path']),
                        codec=self.merger_args['codec'],
                        size=self.merger_args.get('sub2_size', 16),
                        time_offset=self.merger_args.get('sub2_sync', 0)
                    )
                    
                    # Merge subtitles
                    merger.merge()
                    
                    self.progress.emit(
                        f"Successfully merged episode {match['episode_num']} to: {match['output_path']}"
                    )
                
                except Exception as e:
                    self.error.emit(f"Error merging episode {match['episode_num']}: {str(e)}")
                    continue
                
        except Exception as e:
            self.error.emit(f"Critical error in merge worker: {str(e)}")
        
        finally:
            self.finished.emit()

    def stop(self):
        """Stop the merge operation."""
        self.is_running = False 