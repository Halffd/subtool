"""Episode range selector widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QSlider, QGroupBox, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class EpisodeRangeSelector(QWidget):
    """Widget for selecting episode ranges."""
    
    range_changed = pyqtSignal(tuple)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Episode range group
        range_group = QGroupBox("Episode Range")
        range_layout = QVBoxLayout()
        
        # Enable/disable range selection
        self.enable_range = QCheckBox("Enable Episode Range")
        range_layout.addWidget(self.enable_range)
        
        # Controls layout
        controls_layout = QGridLayout()
        
        # Spinboxes
        self.start_spin = QSpinBox()
        self.end_spin = QSpinBox()
        for spin in (self.start_spin, self.end_spin):
            spin.setRange(1, 9999)
            spin.setSingleStep(1)
        
        self.end_spin.setValue(9999)
        
        controls_layout.addWidget(QLabel("Start:"), 0, 0)
        controls_layout.addWidget(self.start_spin, 0, 1)
        controls_layout.addWidget(QLabel("End:"), 0, 2)
        controls_layout.addWidget(self.end_spin, 0, 3)
        
        # Sliders
        self.range_slider = QWidget()
        slider_layout = QHBoxLayout(self.range_slider)
        
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        
        for slider in (self.start_slider, self.end_slider):
            slider.setRange(1, 9999)
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            slider.setTickInterval(100)
            slider_layout.addWidget(slider)
        
        self.end_slider.setValue(9999)
        controls_layout.addWidget(self.range_slider, 1, 0, 1, 4)
        
        range_layout.addLayout(controls_layout)
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)
        
        # Initial state
        self.toggle_range_controls(False)
        self.enable_range.setChecked(False)
    
    def connect_signals(self):
        """Connect all widget signals."""
        self.enable_range.toggled.connect(self.toggle_range_controls)
        self.start_spin.valueChanged.connect(self.start_slider.setValue)
        self.end_spin.valueChanged.connect(self.end_slider.setValue)
        self.start_slider.valueChanged.connect(self.start_spin.setValue)
        self.end_slider.valueChanged.connect(self.end_spin.setValue)
        
        # Connect range changed signals
        for widget in (self.start_spin, self.end_spin):
            widget.valueChanged.connect(self.emit_range_changed)
    
    def toggle_range_controls(self, enabled: bool):
        """Enable or disable range selection controls."""
        for widget in (self.start_spin, self.end_spin, self.range_slider):
            widget.setEnabled(enabled)
        if enabled:
            self.emit_range_changed()
    
    def emit_range_changed(self):
        """Emit the range_changed signal with current values."""
        if self.enable_range.isChecked():
            self.range_changed.emit((self.start_spin.value(), self.end_spin.value()))
        else:
            self.range_changed.emit(None)
    
    def get_range(self) -> tuple[int, int] | None:
        """Get the current episode range if enabled."""
        return (
            (self.start_spin.value(), self.end_spin.value())
            if self.enable_range.isChecked() else None
        ) 