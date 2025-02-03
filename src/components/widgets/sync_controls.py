"""Sync controls widget for subtitle synchronization."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QSlider, QGroupBox, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class SyncControls(QWidget):
    """Widget for controlling subtitle synchronization."""
    
    sync_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Sync group
        sync_group = QGroupBox("Subtitle Synchronization")
        sync_layout = QVBoxLayout()
        
        # Manual sync controls for both subtitles in a grid
        sync_grid = QGridLayout()
        sync_grid.setSpacing(2)
        
        # Sub 1 sync
        sync_grid.addWidget(QLabel("Sub 1:"), 0, 0)
        self.sub1_sync_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub1_sync_slider.setMinimum(-10000)
        self.sub1_sync_slider.setMaximum(10000)
        self.sub1_sync_spinbox = QSpinBox()
        self.sub1_sync_spinbox.setMinimum(-10000)
        self.sub1_sync_spinbox.setMaximum(10000)
        self.sub1_sync_spinbox.setSuffix(" ms")
        sync_grid.addWidget(self.sub1_sync_slider, 0, 1)
        sync_grid.addWidget(self.sub1_sync_spinbox, 0, 2)
        
        # Sub 2 sync
        sync_grid.addWidget(QLabel("Sub 2:"), 1, 0)
        self.sub2_sync_slider = QSlider(Qt.Orientation.Horizontal)
        self.sub2_sync_slider.setMinimum(-10000)
        self.sub2_sync_slider.setMaximum(10000)
        self.sub2_sync_spinbox = QSpinBox()
        self.sub2_sync_spinbox.setMinimum(-10000)
        self.sub2_sync_spinbox.setMaximum(10000)
        self.sub2_sync_spinbox.setSuffix(" ms")
        sync_grid.addWidget(self.sub2_sync_slider, 1, 1)
        sync_grid.addWidget(self.sub2_sync_spinbox, 1, 2)
        
        sync_layout.addLayout(sync_grid)
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
    
    def connect_signals(self):
        """Connect all widget signals."""
        # Connect sync control signals
        self.sub1_sync_slider.valueChanged.connect(self.sub1_sync_spinbox.setValue)
        self.sub1_sync_spinbox.valueChanged.connect(self.sub1_sync_slider.setValue)
        self.sub2_sync_slider.valueChanged.connect(self.sub2_sync_spinbox.setValue)
        self.sub2_sync_spinbox.valueChanged.connect(self.sub2_sync_slider.setValue)
        
        # Connect to sync changed signal
        for widget in (self.sub1_sync_spinbox, self.sub2_sync_spinbox):
            widget.valueChanged.connect(self.emit_sync_changed)
    
    def emit_sync_changed(self):
        """Emit the sync_changed signal with current values."""
        self.sync_changed.emit({
            'sub1_sync': self.sub1_sync_spinbox.value(),
            'sub2_sync': self.sub2_sync_spinbox.value()
        })
    
    def get_sync_values(self) -> dict[str, int]:
        """Get the current sync values."""
        return {
            'sub1_sync': self.sub1_sync_spinbox.value(),
            'sub2_sync': self.sub2_sync_spinbox.value()
        }
    
    def set_sync_values(self, values: dict[str, int]):
        """Set sync values.
        
        Args:
            values: Dictionary with sub1_sync and sub2_sync values
        """
        if 'sub1_sync' in values:
            self.sub1_sync_spinbox.setValue(values['sub1_sync'])
        if 'sub2_sync' in values:
            self.sub2_sync_spinbox.setValue(values['sub2_sync']) 