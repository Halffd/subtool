# Subtitle Merger Tool

A tool for merging and synchronizing subtitle files.

## Running the Application

To run the application, use the provided shell script:

```bash
./run_subtool.sh
```

This script sets the necessary Qt environment variables before launching the application.

## Recent Fixes

The following issues have been fixed:

1. **Qt Platform Plugin Error**: Fixed by setting the correct Qt environment variables in the run script.
   - Added `QT_PLUGIN_PATH=/usr/lib/qt/plugins`
   - Set `QT_QPA_PLATFORM=xcb` instead of using the "dxcb" plugin

2. **Settings Save Errors**: Fixed by improving the handling of UI elements that might not be initialized yet.
   - Added null checks for all UI elements before accessing their values
   - Restructured signal connections to avoid connecting signals before UI elements are fully initialized
   - Improved error handling in settings save methods

3. **Signal Connection Management**: Reorganized how signals are connected to avoid duplicate connections.
   - Created a dedicated `connect_signals` method that runs after UI setup is complete
   - Removed signal connections from individual UI setup methods
   - Added proper error handling for signal connections

## Usage

1. Select the subtitle files or directory containing subtitle files
2. Configure the appearance and synchronization options
3. Click "Merge Subtitles" to process the files
4. Use "Load Previous Configuration" to restore settings from a previous session

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
git clone https://github.com/Halffd/subtitle-merger.git
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.
