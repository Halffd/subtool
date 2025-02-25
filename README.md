# SubTool

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

# Japanese Subtitle Furigana Converter

This tool converts SRT subtitle files to ASS format with furigana (ruby text) for Japanese text. It's designed to work with mpv and other media players that support ASS subtitles.

## Features

- Converts SRT files to ASS format
- Automatically adds furigana (ruby text) to Japanese kanji
- Processes multiple files in batch
- Works with mpv and other media players that support ASS subtitles

## Requirements

- Python 3.6+
- pysrt library (`pip install pysrt`)

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install pysrt
```

3. Make the scripts executable:

```bash
chmod +x srt_to_furigana_ass.py
chmod +x convert_subtitles.sh
```

## Usage

### Basic Usage

To convert all SRT files in the current directory:

```bash
./convert_subtitles.sh
```

### Specify Input and Output Directories

```bash
./convert_subtitles.sh /path/to/input/directory /path/to/output/directory
```

### Customization Options

The script supports several options to customize the appearance of subtitles and furigana:

```bash
# Change font and sizes
./convert_subtitles.sh . . --font "MS Gothic" --font-size 36 --ruby-font-size 18

# Change text and ruby colors (using ASS hex format &HAABBGGRR)
./convert_subtitles.sh . . --text-color "&H00FFFFFF" --ruby-color "&H0000FFFF"

# Change outline and shadow
./convert_subtitles.sh . . --outline-size 3 --shadow-size 3 --outline-color "&H00000000"
```

Available options:
- `--font`: Font to use for subtitles (default: Arial)
- `--font-size`: Font size for main text (default: 48)
- `--ruby-font-size`: Font size for ruby text (default: 24)
- `--text-color`: Color for main text in ASS format (default: &H00FFFFFF - white)
- `--ruby-color`: Color for ruby text in ASS format (default: &H00FFFFFF - white)
- `--outline-color`: Color for text outline (default: &H00000000 - black)
- `--shadow-color`: Color for text shadow (default: &H00000000 - black)
- `--outline-size`: Size of text outline (default: 2)
- `--shadow-size`: Size of text shadow (default: 2)

Note: ASS colors use the format &HAABBGGRR (alpha, blue, green, red).

### Playing with mpv

To play a video with the converted ASS subtitles:

```bash
mpv video.mp4 --sub-file=video.ass
```

## SRT Format Requirements

The script expects SRT files with furigana in parentheses after the kanji. For example:

```
1
00:00:01,000 --> 00:00:05,000
漢字(かんじ)は難(むずか)しいです。
```

This will be converted to ASS format with proper ruby text.

## How It Works

The script uses the ASS subtitle format's ruby text feature to display furigana above kanji characters:

1. It parses SRT files using the `pysrt` library
2. It identifies patterns where kanji is followed by furigana in parentheses
3. It converts these patterns to ASS ruby text tags using the `\rt` tag
4. It creates an ASS file with proper style definitions for both main text and ruby text

### ASS Ruby Text Implementation

The script uses the `\rt` tag for ruby text, which is the correct way to implement furigana in ASS subtitles:

```
{\rt(かんじ)}漢字
```

This displays "かんじ" above "漢字" in the subtitle.

## Troubleshooting

If you see warnings like `Warning: no style named 'かんじ' found` in mpv, it means the ruby text is not implemented correctly. Make sure you're using the latest version of this script which uses the `\rt` tag instead of `\ruby`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
