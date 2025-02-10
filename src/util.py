class EpisodeMatch:
    """Data class for storing matched episode files."""
    episode_num: int
    sub1_path: Path
    sub2_path: Path
    output_path: Optional[Path] = None

class QTextEditLogger(logging.Handler):
    """Custom logging handler that writes to a QTextEdit widget."""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.widget.append(msg)
        except Exception as e:
            print(f"Error writing to log widget: {e}", file=sys.stderr)

class MergeWorker(QThread):
    """Worker thread for handling subtitle merging operations."""
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, matches: List[EpisodeMatch], merger_args: Dict[str, Any]):
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
                    self.progress.emit(f"Processing episode {match.episode_num}")
                    
                    # Create merger instance
                    merger = Merger(output_name=str(match.output_path))
                    
                    # Add subtitles
                    merger.add(str(match.sub1_path), 
                             color=self.merger_args['color'],
                             codec=self.merger_args['codec'])
                    merger.add(str(match.sub2_path))
                    
                    # Merge subtitles
                    merger.merge()
                    
                    self.progress.emit(
                        f"Successfully merged episode {match.episode_num} to: {match.output_path}"
                    )
                
                except Exception as e:
                    self.error.emit(f"Error merging episode {match.episode_num}: {str(e)}")
                    continue
                
        except Exception as e:
            self.error.emit(f"Critical error in merge worker: {str(e)}")
        
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False

class EpisodeRangeSelector(QWidget):
    """Widget for selecting episode ranges."""
    range_changed = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
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

    def get_range(self) -> Optional[Tuple[int, int]]:
        """Get the current episode range if enabled."""
        return (
            (self.start_spin.value(), self.end_spin.value())
            if self.enable_range.isChecked() else None
        )
