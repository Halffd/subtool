#!/bin/bash

# Convert SRT files to ASS with furigana
# Usage: ./convert_subtitles.sh [input_directory] [output_directory] [options]
#
# Options:
#   --font FONT               Font to use for subtitles (default: Arial)
#   --font-size SIZE          Font size for main text (default: 48)
#   --ruby-font-size SIZE     Font size for ruby text (default: 24)
#   --text-color COLOR        Color for main text in ASS format (&HAABBGGRR) (default: &H00FFFFFF)
#   --ruby-color COLOR        Color for ruby text in ASS format (&HAABBGGRR) (default: &H00FFFFFF)
#   --outline-color COLOR     Color for text outline in ASS format (&HAABBGGRR) (default: &H00000000)
#   --shadow-color COLOR      Color for text shadow in ASS format (&HAABBGGRR) (default: &H00000000)
#   --outline-size SIZE       Size of text outline (default: 2)
#   --shadow-size SIZE        Size of text shadow (default: 2)

echo "Japanese Subtitle Furigana Converter"
echo "-----------------------------------"
echo "This script converts SRT subtitle files to ASS format with furigana"
echo "using proper ruby text tags (\rt) for display in media players like mpv."
echo "Now using pysubs2 for better compatibility and reliability."
echo ""

# Make sure the Python script is executable
chmod +x srt_to_furigana_ass.py

# Set default directories
INPUT_DIR="${1:-.}"
OUTPUT_DIR="${2:-$INPUT_DIR}"

# Shift the first two arguments if they exist
if [ $# -ge 1 ]; then
    shift
    if [ $# -ge 1 ]; then
        shift
    fi
fi

# Run the Python script with all remaining arguments
./srt_to_furigana_ass.py "$INPUT_DIR" "$OUTPUT_DIR" "$@"

echo ""
echo "Conversion complete. You can play the videos with mpv using the ASS subtitles."
echo "Example: mpv video.mp4 --sub-file=video.ass"
echo ""
echo "Note: This script uses the \rt tag for ruby text, which is the correct way"
echo "to implement furigana in ASS subtitles and avoids warnings in mpv."
echo ""
echo "Customization Examples:"
echo "  ./convert_subtitles.sh . . --font \"MS Gothic\" --font-size 36 --ruby-font-size 18"
echo "  ./convert_subtitles.sh . . --text-color \"&H0000FFFF\" --ruby-color \"&H00FF00FF\"" 