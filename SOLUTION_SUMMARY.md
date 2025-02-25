# Japanese Subtitle Furigana Solution

## Overview

This solution provides a complete workflow for displaying Japanese subtitles with furigana (ruby text) in the mpv media player. The implementation converts SRT subtitle files with furigana notation to ASS format, which properly supports ruby text display.

## Components

1. **srt_to_furigana_ass.py**: Python script that converts SRT files to ASS format with proper ruby text implementation.
2. **convert_subtitles.sh**: Shell script wrapper for easy usage of the Python script.
3. **sample.srt**: Example SRT file with furigana notation.
4. **demo.mp4**: Demo video for testing the subtitles.

## How It Works

1. The user creates SRT subtitle files with furigana in parentheses after kanji:
   ```
   漢字(かんじ)は難(むずか)しいです。
   ```

2. The conversion script parses these files and converts them to ASS format, using the proper `\rt` tag for ruby text:
   ```
   {\rt(かんじ)}漢字{\rt(むずか)}は難しいです。
   ```

3. The ASS file includes style definitions for both the main text and ruby text, allowing for customization of font, size, color, and other properties.

4. The user plays the video with mpv, specifying the ASS subtitle file:
   ```
   mpv video.mp4 --sub-file=video.ass
   ```

## Key Features

### Proper Ruby Text Implementation

The solution uses the correct ASS tag `\rt` for ruby text, avoiding the common mistake of using `\ruby` which causes warnings in mpv about missing styles.

### Extensive Customization Options

The script supports customization of:
- Font family
- Font size (main text and ruby text)
- Text color (main text and ruby text)
- Outline color and size
- Shadow color and size

### Easy to Use

The shell script wrapper makes it simple to convert files with a single command, with sensible defaults and clear documentation.

## Usage Examples

### Basic Usage

```bash
./convert_subtitles.sh
```

### With Customization

```bash
./convert_subtitles.sh . . --font "MS Gothic" --font-size 36 --ruby-font-size 18 --text-color "&H00FFFFFF" --ruby-color "&H0000FFFF" --outline-size 3 --shadow-size 3
```

## Troubleshooting

If you see warnings about missing styles in mpv, ensure you're using the latest version of the script which implements ruby text correctly with the `\rt` tag instead of `\ruby`.

## Future Improvements

Potential enhancements for the future:
- GUI interface for easier customization
- Preview functionality to see how subtitles will look
- Support for additional subtitle formats
- Integration with automatic furigana generation tools 