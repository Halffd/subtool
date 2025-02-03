#!/bin/python
import os
import argparse
from main import Merger

def detect_os_codec():
    """
    Detects the operating system and returns the appropriate codec.
    """
    if os.name == "nt":  # Windows
        return "windows-1256"
    else:  # Other OS (Linux, macOS, etc.)
        return "utf-8"


def merge_subtitles_cli(subtitle1, subtitle2, output_name, color, codec):
    """
    Handles merging subtitles via provided arguments.
    """
    try:
        merger = Merger(output_name=output_name)
        merger.add(subtitle1, color=color, codec=codec)
        merger.add(subtitle2)
        merger.merge()
        print(f"Subtitles merged successfully! Output: {output_name}")
    except Exception as e:
        print(f"Error during merging: {e}")


def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(
        description="Merge two subtitle files into one with optional color and codec settings."
    )
    parser.add_argument(
        "subtitle1", help="Path to the first subtitle file (e.g., fa.srt)"
    )
    parser.add_argument(
        "subtitle2", help="Path to the second subtitle file (e.g., en.srt)"
    )
    parser.add_argument(
        "output_name",
        nargs="?",
        default=None,
        help="Name of the output subtitle file (default: <subtitle1>_merged.srt)",
    )
    parser.add_argument(
        "--color",
        default="default",
        help="Text color for the first subtitle (e.g., yellow, cyan). Default: no color.",
    )
    parser.add_argument(
        "--codec",
        default=None,
        help="Codec for reading the first subtitle file (e.g., utf-8, windows-1256). "
             "If not provided, it will be detected based on the OS.",
    )

    # Parse arguments
    args = parser.parse_args()

    # Determine output name
    output_name = args.output_name or f"{args.subtitle1.split('.')[0]}_merged.srt"

    # Determine Codec
    codec = args.codec or detect_os_codec()

    # Call the merge function
    merge_subtitles_cli(args.subtitle1, args.subtitle2, output_name, args.color, codec)


if __name__ == "__main__":
    main()

