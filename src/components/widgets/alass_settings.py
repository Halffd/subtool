"""ALASS settings widget for subtitle synchronization."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QDoubleSpinBox, QGroupBox, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class ALASSSettings(QWidget):
    """Widget for ALASS synchronization settings."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # ALASS settings group
        alass_group = QGroupBox("ALASS Settings")
        alass_layout = QVBoxLayout()
        
        # Enable ALASS checkbox
        self.use_alass = QCheckBox("Enable ALASS Auto-sync")
        alass_layout.addWidget(self.use_alass)
        
        # Disable FPS guessing checkbox
        self.disable_fps_guessing = QCheckBox("Disable FPS Guessing")
        self.disable_fps_guessing.setToolTip("Disable automatic FPS detection")
        alass_layout.addWidget(self.disable_fps_guessing)
        
        # ALASS parameters grid
        params_grid = QGridLayout()
        
        # Interval
        params_grid.addWidget(QLabel("Interval:"), 0, 0)
        self.alass_interval = QSpinBox()
        self.alass_interval.setRange(0, 10000)
        self.alass_interval.setValue(100)
        self.alass_interval.setSuffix(" ms")
        params_grid.addWidget(self.alass_interval, 0, 1)
        
        # Split penalty
        params_grid.addWidget(QLabel("Split Penalty:"), 1, 0)
        self.alass_split_penalty = QDoubleSpinBox()
        self.alass_split_penalty.setRange(0, 1000)
        self.alass_split_penalty.setValue(10)
        self.alass_split_penalty.setSingleStep(0.1)
        params_grid.addWidget(self.alass_split_penalty, 1, 1)
        
        # FPS settings
        params_grid.addWidget(QLabel("Sub FPS:"), 2, 0)
        self.alass_sub_fps = QDoubleSpinBox()
        self.alass_sub_fps.setRange(0, 120)
        self.alass_sub_fps.setValue(23.976)
        self.alass_sub_fps.setSingleStep(0.001)
        params_grid.addWidget(self.alass_sub_fps, 2, 1)
        
        params_grid.addWidget(QLabel("Ref FPS:"), 3, 0)
        self.alass_ref_fps = QDoubleSpinBox()
        self.alass_ref_fps.setRange(0, 120)
        self.alass_ref_fps.setValue(23.976)
        self.alass_ref_fps.setSingleStep(0.001)
        params_grid.addWidget(self.alass_ref_fps, 3, 1)
        
        alass_layout.addLayout(params_grid)
        alass_group.setLayout(alass_layout)
        layout.addWidget(alass_group)
    
    def connect_signals(self):
        """Connect all widget signals."""
        # Connect all settings to emit changes
        self.use_alass.toggled.connect(self.emit_settings_changed)
        self.disable_fps_guessing.toggled.connect(self.emit_settings_changed)
        self.alass_interval.valueChanged.connect(self.emit_settings_changed)
        self.alass_split_penalty.valueChanged.connect(self.emit_settings_changed)
        self.alass_sub_fps.valueChanged.connect(self.emit_settings_changed)
        self.alass_ref_fps.valueChanged.connect(self.emit_settings_changed)
    
    def emit_settings_changed(self):
        """Emit the settings_changed signal with current values."""
        self.settings_changed.emit(self.get_settings())
    
    def get_settings(self) -> dict:
        """Get current ALASS settings."""
        return {
            'use_alass': self.use_alass.isChecked(),
            'disable_fps_guessing': self.disable_fps_guessing.isChecked(),
            'alass_interval': self.alass_interval.value(),
            'alass_split_penalty': self.alass_split_penalty.value(),
            'alass_sub_fps': self.alass_sub_fps.value(),
            'alass_ref_fps': self.alass_ref_fps.value()
        }
    
    def set_settings(self, settings: dict):
        """Set ALASS settings.
        
        Args:
            settings: Dictionary with ALASS settings
        """
        if 'use_alass' in settings:
            self.use_alass.setChecked(settings['use_alass'])
        if 'disable_fps_guessing' in settings:
            self.disable_fps_guessing.setChecked(settings['disable_fps_guessing'])
        if 'alass_interval' in settings:
            self.alass_interval.setValue(settings['alass_interval'])
        if 'alass_split_penalty' in settings:
            self.alass_split_penalty.setValue(settings['alass_split_penalty'])
        if 'alass_sub_fps' in settings:
            self.alass_sub_fps.setValue(settings['alass_sub_fps'])
        if 'alass_ref_fps' in settings:
            self.alass_ref_fps.setValue(settings['alass_ref_fps']) 