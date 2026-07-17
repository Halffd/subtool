# Subtitle Merger Tool

A tool to merge subtitles from multiple languages, with enhanced automatic detection for various filename patterns.

## Features

- **GUI Mode**: Interactive graphical interface for easy subtitle merging
- **CLI Mode**: Command-line interface for automation and batch processing
- Merge subtitles from two different languages into a single file
- Support for both manual filename pattern specification and automatic detection
- Toggle between pattern modes with a convenient UI button
- Automatic detection of episode numbers from filenames
- Support for various subtitle formats
- Batch processing of entire directories
- Customizable colors, fonts, and timing
- SVG filtering and furigana support
- ALASS integration for automatic synchronization

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

### GUI Mode

#### Directory Mode

1. Select the "Directory" tab
2. Choose whether to use automatic detection or manual patterns with the toggle button
3. If using manual patterns:
   - Set subtitle filename patterns for both languages
   - Set the episode number pattern
4. Select the input directory containing subtitle files
5. Select the output directory for merged files
6. Click "Merge All Files" to process

#### Single Files Mode

1. Select the "Single Files" tab
2. Choose the first subtitle file
3. Choose the second subtitle file
4. Select an output file
5. Click "Merge Files" to process

### CLI Mode

The tool also supports command-line operations for automation and batch processing.

#### Single File Merge

```bash
# Basic usage
python subtool.py single input1.srt input2.srt output.srt

# With custom options
python subtool.py single input1.srt input2.srt output.srt --color blue --sub1-size 20 --sub2-size 18 --sub1-delay 100

# Convert to ASS format with furigana
python subtool.py single input1.srt input2.srt output.srt --convert-to-ass
```

#### Batch Processing

```bash
# Basic batch processing
python subtool.py batch /path/to/subtitles /path/to/videos

# With custom patterns
python subtool.py batch /path/to/subtitles /path/to/videos --sub1-pattern ".*jpn.*\.srt$" --sub2-pattern ".*eng.*\.srt$"

# With custom options
python subtool.py batch /path/to/subtitles /path/to/videos --sub1-delay 50 --sub2-delay -25 --codec utf-8

# With ALASS auto-sync
python subtool.py batch /path/to/subtitles /path/to/videos --enable-alass-sync --alass-interval 200 --alass-split-penalty 5.0
```

#### Available Options

**Single File Options:**
- `--color`: Color for first subtitle (white, yellow, red, blue, green, or #RRGGBB)
- `--codec`: Text encoding (default: utf-8)
- `--sub1-size`, `--sub2-size`: Font sizes for subtitles
- `--sub1-delay`, `--sub2-delay`: Time delays in milliseconds
- `--sub1-bold`, `--sub2-bold`: Make subtitles bold
- `--enable-svg-filtering`: Enable SVG filtering
- `--remove-text-entries`: Remove text entries
- `--preserve-svg`: Preserve SVG paths
- `--convert-to-ass`: Convert output to ASS format with furigana

**Batch Processing Options:**
- `--output-dir`: Output directory (defaults to input directory)
- `--sub1-pattern`, `--sub2-pattern`: Regex patterns for subtitle files
- `--sub1-episode-pattern`, `--sub2-episode-pattern`: Regex patterns for episode numbers
- `--enable-alass-sync`: Enable ALASS auto-sync with video files
- `--alass-path`: Path to ALASS executable
- `--alass-interval`: ALASS interval parameter in ms (default: 100)
- `--alass-split-penalty`: ALASS split penalty parameter (default: 10.0)
- `--alass-sub-fps`: ALASS subtitle FPS (default: 23.976)
- `--alass-ref-fps`: ALASS reference FPS (default: 23.976)
- `--disable-fps-guessing`: Disable FPS guessing in ALASS
- All single file options are also available for batch processing

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
