# SubTool

A PyQt6-based GUI application for merging multiple SRT subtitle files into a single file. The application supports both individual file merging and directory-based batch merging.

## Features

- Merge multiple SRT subtitle files into a single file
- Two operation modes:
  - Single Files: Select and merge individual subtitle files
  - Directory: Merge subtitle files in a directory based on file patterns
- Convert SRT files to ASS format with furigana (ruby text) support
- Automatic furigana generation for Japanese text
- Dark theme UI
- Progress tracking for merge operations
- Graceful error handling

## Requirements

- Python 3.6+
- PyQt6
- pysrt
- pysubs2
- janome (for automatic furigana generation)
- jaconv
- regex

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
- Advanced styling with precise positioning and colored text
- Professional-quality subtitles matching anime fansub standards

## Automatic Furigana Generation

The tool now includes automatic furigana generation for Japanese text. This feature uses the Janome tokenizer to analyze Japanese text and automatically add furigana to kanji characters. To use this feature:

1. Enable the "Convert to ASS with Furigana" option in the application
2. Process your subtitle files as usual
3. The tool will automatically generate furigana for all kanji in the subtitles

This is especially useful for Japanese language learners who want to see the readings of kanji characters while watching videos.

## Manual Furigana Format

If you prefer to manually add furigana, the tool also supports the following format in SRT files:

```
漢字(かんじ)は難(むずか)しいです。
```

This will be converted to ASS format with proper ruby text.

## Advanced Styling

The tool now supports advanced styling that matches professional anime subtitles:

- Each character or word is positioned precisely on screen
- Ruby text (furigana) is placed directly above the base text
- Colored text is supported with special color tags
- Underlines are added beneath text with furigana
- Multiple subtitle lines with proper vertical spacing

Example of color tags that can be used in SRT files:

```
<font color="darkblue">青い</font>空を<font color="purple">見上げる</font>
```

Available colors include:
- darkblue
- lightblue
- purple
- orange
- darkgreen
- red
- blue
- green
- yellow
- cyan
- magenta
- white
- black

## Playing with mpv

To play a video with the converted ASS subtitles:

```bash
mpv video.mp4 --sub-file=video.ass
```

## ASS Ruby Text Implementation

The tool uses two different methods for ruby text:

1. Simple mode: Uses the `\rt` tag for basic ruby text
2. Advanced mode: Creates separate dialogue entries for each text element with precise positioning

The advanced mode creates subtitles that look like this in the ASS file:

```
Dialogue: 3,0:00:01.00,0:00:05.30,Default,,0,0,0,,{\pos(666,903)}漢字
Dialogue: 2,0:00:01.00,0:00:05.30,Ruby,,0,0,0,,{\pos(666,856)}かんじ
Dialogue: 1,0:00:01.00,0:00:05.30,Underline,,0,0,0,,{\pos(0,0)}{\c&H4E4EF1&}{\p1}m 613 940 l 719 940 719 944 613 944{\p0}{\c}
```

This creates professional-quality subtitles with perfect alignment and styling.

## Customization Options

The ASS conversion supports several options to customize the appearance of subtitles and furigana:

- Font family (default: MS Gothic for Japanese text)
- Font size for main text and ruby text
- Text color for main text and ruby text
- Outline and shadow settings
- Advanced styling with separate dialogue entries

## Troubleshooting

If you see warnings like `Warning: no style named 'かんじ' found` in mpv, it means the ruby text is not implemented correctly. Make sure you're using the latest version of this tool which uses the `\rt` tag instead of `\ruby`.

If the advanced styling doesn't display correctly in your media player, try using a player with better ASS subtitle support, such as mpv or VLC.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
