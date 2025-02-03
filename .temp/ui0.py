import sys
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget
)
from main import Merger


class SubtitleMergerApp(QMainWindow):
    """
    A PyQt5-based GUI application for merging subtitle files.
    Users can select individual subtitle files or a directory containing subtitles.
    Regex patterns are used to identify the primary and secondary subtitles in case of directories.
    """

    def __init__(self):
        super().__init__()
        self.files = []  # List to store selected files
        self.regex1 = None  # Regex for matching primary subtitles
        self.regex2 = None  # Regex for matching secondary subtitles
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface.
        """
        self.setWindowTitle("Subtitle Merger")
        self.setGeometry(200, 200, 400, 250)

        # Widgets
        self.status_label = QLabel("Select files or directory to merge subtitles", self)
        self.status_label.setWordWrap(True)
        self.select_file_button = QPushButton("Select Files", self)
        self.select_dir_button = QPushButton("Select Directory", self)
        self.merge_button = QPushButton("Merge Subtitles", self)

        # Connect buttons to their respective methods
        self.select_file_button.clicked.connect(self.select_files)
        self.select_dir_button.clicked.connect(self.select_directory)
        self.merge_button.clicked.connect(self.merge_subtitles)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.select_file_button)
        layout.addWidget(self.select_dir_button)
        layout.addWidget(self.merge_button)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def select_files(self):
        """
        Opens a file dialog for the user to select subtitle files.
        """
        files, _ = QFileDialog.getOpenFileNames(self, "Select Subtitle Files", "", "Subtitle Files (*.srt)")
        if files:
            self.files = files
            self.status_label.setText(f"Selected files: {', '.join(files)}")

    def select_directory(self):
        """
        Opens a directory picker for the user to select a directory containing subtitle files.
        Filters files using regex1 and regex2 if set.
        """
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.files = []  # Reset file list
            all_files = list(Path(directory).rglob("*.srt"))
            if all_files:
                # Ask user for regex patterns
                regex1, regex2 = self.get_regex_patterns()
                self.regex1, self.regex2 = regex1, regex2

                for file in all_files:
                    if regex1 and re.search(regex1, file.name):
                        self.files.append(file)
                    elif regex2 and re.search(regex2, file.name):
                        self.files.append(file)

                self.status_label.setText(
                    f"Selected directory: {directory}\nMatched {len(self.files)} files."
                )
            else:
                self.status_label.setText("No .srt files found in the selected directory.")

    def get_regex_patterns(self):
        """
        Prompts the user to enter regex patterns for filtering subtitles.
        Returns two regex strings for primary and secondary subtitles.
        """
        # Replace this section with a PyQt input dialog or a custom widget for entering regex
        regex1 = input("Enter regex pattern for primary subtitles (regex1): ").strip()
        regex2 = input("Enter regex pattern for secondary subtitles (regex2): ").strip()
        return regex1, regex2

    def merge_subtitles(self):
        """
        Merges the selected subtitles into a single output file.
        Uses the `Merger` class from `main.py`.
        """
        if not self.files:
            self.status_label.setText("No files selected for merging!")
            return

        output_name = "merged_output.srt"
        codec_primary = "utf-8"  # Default codec for primary subtitles
        codec_secondary = "utf-8"  # Default codec for secondary subtitles

        try:
            merger = Merger(output_name=output_name)
            for file in self.files:
                if self.regex1 and re.search(self.regex1, file.name):
                    merger.add(str(file), color="yellow", codec=codec_primary)
                elif self.regex2 and re.search(self.regex2, file.name):
                    merger.add(str(file), codec=codec_secondary)
                else:
                    self.status_label.setText(
                        f"File '{file.name}' does not match any regex. Skipping..."
                    )
            merger.merge()
            self.status_label.setText(f"Subtitles merged successfully! Output: {output_name}")
        except Exception as e:
            self.status_label.setText(f"Error during merging: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleMergerApp()
    window.show()
    sys.exit(app.exec_())

