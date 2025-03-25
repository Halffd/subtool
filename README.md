# Subtitle Merger Tool

A tool to merge subtitles from multiple languages, with enhanced automatic detection for various filename patterns.

## Features

- Merge subtitles from two different languages into a single file
- Support for both manual filename pattern specification and automatic detection
- Toggle between pattern modes with a convenient UI button
- Automatic detection of episode numbers from filenames
- Support for various subtitle formats
- Batch processing of entire directories

## Installation

### Prerequisites

- Python 3.6 or higher
- PyQt6 (for the GUI)

### Setup

1. Clone this repository
2. Run the provided script:

```bash
./run_subtool.sh
```

This script will:
- Create a virtual environment if needed
- Install all required dependencies
- Configure the Qt environment
- Launch the application

## Usage

### Directory Mode

1. Select the "Directory" tab
2. Choose whether to use automatic detection or manual patterns with the toggle button
3. If using manual patterns:
   - Set subtitle filename patterns for both languages
   - Set the episode number pattern
4. Select the input directory containing subtitle files
5. Select the output directory for merged files
6. Click "Merge All Files" to process

### Single Files Mode

1. Select the "Single Files" tab
2. Choose the first subtitle file
3. Choose the second subtitle file
4. Select an output file
5. Click "Merge Files" to process

## Automatic Detection

When automatic detection is enabled, the tool will:
- Scan the directory for subtitle files
- Identify patterns in filenames
- Group subtitles by episode
- Detect the subtitle language

Supported episode number formats include:
- `S01E02` format
- `01x02` format
- Simple numeric formats (e.g., `Episode 5` or just `5`)

## Troubleshooting

If you encounter issues with Qt plugins, try setting the correct Qt plugin path:

```bash
export QT_PLUGIN_PATH=/path/to/qt/plugins
export QT_QPA_PLATFORM=xcb  # For X11 systems
```

Or simply use the provided `run_subtool.sh` script which handles this automatically.
