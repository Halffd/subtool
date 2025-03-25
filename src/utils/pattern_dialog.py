from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QGroupBox, QRadioButton,
    QButtonGroup
)
from PyQt6.QtCore import Qt
from pathlib import Path

class PatternConflictDialog(QDialog):
    """Dialog for resolving pattern conflicts when multiple files match the same episode."""
    
    def __init__(self, conflicts, parent=None):
        """
        Initialize the dialog.
        
        Args:
            conflicts: Dictionary with structure:
                {
                    'episode': str,
                    'language': str,
                    'patterns': [
                        {
                            'pattern': str,
                            'description': str,
                            'examples': [str, ...],
                            'matches': [str, ...]
                        },
                        ...
                    ]
                }
        """
        super().__init__(parent)
        self.conflicts = conflicts
        self.selected_pattern = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Pattern Conflict Resolution")
        layout = QVBoxLayout()
        
        # Add description
        desc = QLabel(
            f"Multiple patterns found for {self.conflicts['language']} subtitles "
            f"(Episode {self.conflicts['episode']}).\n"
            "Please select which pattern to use:"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Create pattern selection group
        pattern_group = QButtonGroup(self)
        pattern_group.buttonClicked.connect(self.on_pattern_selected)
        
        for i, pattern_info in enumerate(self.conflicts['patterns']):
            pattern_box = QGroupBox()
            pattern_layout = QVBoxLayout()
            
            # Add radio button with pattern
            radio = QRadioButton(f"Pattern: {pattern_info['pattern']}")
            pattern_group.addButton(radio, i)
            pattern_layout.addWidget(radio)
            
            # Add description
            if pattern_info['description']:
                desc_label = QLabel(pattern_info['description'])
                desc_label.setWordWrap(True)
                pattern_layout.addWidget(desc_label)
            
            # Add example matches
            if pattern_info['matches']:
                examples_label = QLabel("Matching files:")
                pattern_layout.addWidget(examples_label)
                
                examples_list = QListWidget()
                for example in pattern_info['matches']:
                    examples_list.addItem(str(Path(example).name))
                examples_list.setMaximumHeight(100)
                pattern_layout.addWidget(examples_list)
            
            pattern_box.setLayout(pattern_layout)
            layout.addWidget(pattern_box)
        
        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def on_pattern_selected(self, button):
        """Handle pattern selection."""
        index = self.findChild(QButtonGroup).id(button)
        self.selected_pattern = self.conflicts['patterns'][index]
    
    @staticmethod
    def resolve_conflicts(conflicts, parent=None):
        """
        Show the dialog and return the selected pattern.
        
        Returns:
            dict: Selected pattern info or None if cancelled
        """
        dialog = PatternConflictDialog(conflicts, parent)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted and dialog.selected_pattern:
            return dialog.selected_pattern
        return None 