# Subtitle Merger

A PyQt6-based GUI application for merging multiple SRT subtitle files into a single file. The application supports both individual file merging and directory-based batch merging.

## Features

- Merge multiple SRT subtitle files into a single file
- Two operation modes:
  - Single Files: Select and merge individual subtitle files
  - Directory: Merge subtitle files in a directory based on file patterns
- Dark theme UI
- Progress tracking for merge operations
- Graceful error handling

## Requirements

- Python 3.6+
- PyQt6
- pysrt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/subtitle-merger.git
cd subtitle-merger
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python subtool.py
```

### Single Files Mode
1. Click "Add Files" to select SRT files to merge
2. Use "Remove Selected" or "Clear All" to modify the file list
3. Click "Merge Subtitles" and select an output location
4. Wait for the merge to complete

### Directory Mode
1. Select an input directory containing SRT files
2. Enter a file pattern (e.g., "*_en.srt, *_fr.srt")
3. Select an output directory
4. Click "Merge Subtitles" to start the batch merge
5. Wait for the merge to complete

## License

This project is licensed under the MIT License - see the LICENSE file for details.
