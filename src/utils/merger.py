#!/usr/bin/env python
# author: Iraj Jelodari

import datetime
import codecs
import re
import logging

RED = '#FF003B'
BLUE = '#00ADFF'
GREEN = '#B4FF00'
WHITE = '#FFFFFF'
YELLOW = '#FFEB00'

TIME_PATTERN = r'\d{1,2}:\d{1,2}:\d{1,2},\d{1,5} --> \d{1,2}:\d{1,2}:\d{1,2},\d{1,5}\r\n'


class Merger():
    """
    SRT Merger allows you to merge subtitle files, no matter what language
    are the subtitles encoded in. The result of this merge will be a new subtitle
    file which will display subtitles from each merged file.
    """

    def __init__(self, output_path=".", output_name='subtitle_name.srt', output_encoding='utf-8'):
        self.timestamps = []
        self.subtitles = []
        self.lines = []
        self.output_path = output_path
        self.output_name = output_name
        self.output_encoding = output_encoding
        self.svg_filter_enabled = False
        self.remove_text_entries = False
        self.seen_svg_timestamps = set()
        # Initialize logger
        self.logger = logging.getLogger('merger')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _insert_bom(self, content, encoding):
        encoding = encoding.replace('-', '')\
            .replace('_', '')\
            .replace(' ', '')\
            .upper()
        if encoding in ['UTF64LE', 'UTF16', 'UTF16LE']:
            return codecs.BOM + content
        if encoding in ['UTF8']:
            return codecs.BOM_UTF8 + content
        if encoding in ['UTF32LE']:
            return codecs.BOM_UTF32_LE + content
        if encoding in ['UTF64BE']:
            return codecs.BOM_UTF64_BE + content
        if encoding in ['UTF16BE']:
            return codecs.BOM_UTF32_BE + content
        if encoding in ['UTF32BE']:
            return codecs.BOM_UTF32_BE + content
        if encoding in ['UTF32']:
            return codecs.BOM_UTF32 + content
        return content

    def _set_subtitle_color(self, subtitle, color):
        """
        Set a color for subtitle text.
        
        Args:
            subtitle (str): The subtitle text
            color (str): Color in HTML format (#RRGGBB) or color name
            
        Returns:
            str: Subtitle text with ASS color tags
        """
        if not color:
            return subtitle
        
        # Convert hex color to ASS format (BGR)
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
        else:
            # Use predefined color mapping
            ass_color = color
        
        # Add ASS color tags
        return f"{{\\c{ass_color}}}{subtitle}{{\\c}}"

    def _put_subtitle_top(self, subtitle):
        """
        Put the subtitle at the top of the screen 
        """
        return '{\\an8}' + subtitle

    def _is_svg_path(self, text):
        """
        Check if the text contains an SVG path.
        
        Args:
            text (str): The subtitle text
            
        Returns:
            bool: True if the text contains an SVG path, False otherwise
        """
        return bool(re.search(r'{\an\d}m\s+\d+\.\d+\s+\d+\.\d+\s+b', text))

    def _set_subtitle_style(self, subtitle, color=None, size=None, bold=False, preserve_svg=False):
        """
        Apply style (color, size, and thickness) to subtitle text while preserving formatting
        
        Args:
            subtitle (str): The subtitle text
            color (str): Color in HTML format (#RRGGBB) or color name
            size (int): Font size in pixels
            bold (bool): Whether to make the text bold
            preserve_svg (bool): Whether to preserve SVG path data
            
        Returns:
            str: Styled subtitle text with font tags
        """
        # Check if this is an SVG path and we should preserve it
        if preserve_svg and self._is_svg_path(subtitle):
            # For SVG paths, we want to preserve the original formatting
            # Extract font face if present in the original line
            face_match = re.search(r'<font[^>]*face="([^"]+)"[^>]*>', subtitle.strip())
            face = face_match.group(1) if face_match else "Brady Bunch Remastered"
            
            # Extract size if present
            size_match = re.search(r'<font[^>]*size="([^"]+)"[^>]*>', subtitle.strip())
            svg_size = size_match.group(1) if size_match else "48"
            
            # Extract color if present
            color_match = re.search(r'<font[^>]*color="([^"]+)"[^>]*>', subtitle.strip())
            svg_color = color_match.group(1) if color_match else "#FFFFFF"
            
            # Extract position if present
            position_match = re.search(r'{\\an(\d)}', subtitle)
            position = position_match.group(1) if position_match else "7"
            
            # Extract the SVG path data
            svg_path_match = re.search(r'({\an\d}m\s+\d+\.\d+.+)', subtitle)
            if svg_path_match:
                svg_path = svg_path_match.group(1)
                return f'<font face="{face}" size="{svg_size}" color="{svg_color}">{svg_path}</font>\n'
            
            # If we couldn't extract the path, return the original
            return subtitle + '\n'
        
        # Split text into lines and process each line
        lines = subtitle.strip().split('\n')
        styled_lines = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Extract all text content, ignoring all HTML tags
            # This is a more aggressive approach that ensures we get just the raw text
            raw_text = re.sub(r'<[^>]*>', '', line.strip())
            
            # Extract font face if present in the original line
            face_match = re.search(r'<font[^>]*face="([^"]+)"[^>]*>', line.strip())
            face = face_match.group(1) if face_match else None
            
            # Build font attributes
            font_attrs = []
            if face:
                font_attrs.append(f'face="{face}"')
            if size is not None:
                font_attrs.append(f'size="{size}"')
            if color:
                font_attrs.append(f'color="{color}"')
            
            # Create the styled line with consistent formatting
            if bold:
                styled_lines.append(f'<font {" ".join(font_attrs)}><b>{raw_text}</b></font>')
            else:
                styled_lines.append(f'<font {" ".join(font_attrs)}>{raw_text}</font>')
        
        # Join lines with newlines and add final newline
        return '\n'.join(styled_lines) + '\n'

    def _split_dialogs(self, dialogs, subtitle, color=None, size=None, top=False, bold=False, preserve_svg=False):
        """Split and process subtitle dialogs with styling."""
        for dialog in dialogs:
            # Clean up dialog text
            if dialog.startswith('\r\n'):
                dialog = dialog.replace('\r\n', '', 1)
            if dialog.startswith('\n'):
                dialog = dialog[1:]
            if dialog == '' or dialog == '\n' or dialog.rstrip().lstrip() == '':
                continue
                
            try:
                # Extract timestamp
                if dialog.startswith('\r\n'):
                    dialog = dialog[2:]
                time = dialog.split('\n', 2)[1].split('-->')[0].split(',')[0]
                timestamp = datetime.datetime.strptime(time, '%H:%M:%S').timestamp()
                
                # Extract text content
                text_and_time = dialog.split('\n', 1)[1]
                texts = text_and_time.split('\n')[1:]
                time = text_and_time.split('\n')[0]
                
                # Combine text lines
                text = '\n'.join(line for line in texts if line.strip())
                if not text:
                    continue
                
                # Check if this is an SVG path
                is_svg = self._is_svg_path(text)
                
                # If SVG filtering is enabled, handle SVG paths specially
                if self.svg_filter_enabled and is_svg:
                    # Skip duplicate SVG entries for the same timestamp
                    if timestamp in self.seen_svg_timestamps:
                        continue
                    self.seen_svg_timestamps.add(timestamp)
                
                # Skip text entries if remove_text_entries is True and this is not an SVG path
                if self.remove_text_entries and not is_svg:
                    continue
                
                # Apply style (color and size) to text
                text = self._set_subtitle_style(text, color, size, bold, preserve_svg)
                
                # Add position if needed
                if top and not is_svg:  # Don't add top position to SVG paths as they have their own positioning
                    text = self._put_subtitle_top(text)
                    
                # Format final text with timestamp
                text_and_time = f'{time}\n{text}'
                
                # Handle multiple dialogs at same timestamp
                prev_dialog = subtitle['dialogs'].get(timestamp, '')
                prev_dialog_without_timestamp = re.sub(TIME_PATTERN, '', prev_dialog)
                
                if re.findall(TIME_PATTERN, text_and_time):
                    time = re.findall(TIME_PATTERN, text_and_time)[0]
                    
                subtitle['dialogs'][timestamp] = text_and_time + prev_dialog_without_timestamp
                self.timestamps.append(timestamp)
                
            except Exception as e:
                continue

    def _encode(self, text):
        codec = self.output_encoding
        try:
            return bytes(text, encoding=codec)
        except Exception as e:
            print('Problem in "%s" to encoing by %s. \nError: %s' %
                  (repr(text), codec, e))
            return b'An error has been occured in encoing by specifed `output_encoding`'

    def add(self, subtitle_address, codec="utf-8", color=WHITE, size=None, top=False, time_offset=0, bold=False, preserve_svg=False):
        """
        Add a subtitle file to be merged
        
        Args:
            subtitle_address (str): Path to subtitle file
            codec (str): Character encoding of the subtitle file
            color (str): Hex color code for the subtitle text
            size (int): Font size in pixels
            top (bool): Whether to position subtitle at top of screen
            time_offset (int): Time offset in milliseconds
            bold (bool): Whether to make the text bold
            preserve_svg (bool): Whether to preserve SVG path data
        """
        subtitle = {
            'address': subtitle_address,
            'codec': codec,
            'color': color,
            'size': size,
            'bold': bold,
            'dialogs': {}
        }
        
        # List of encodings to try
        encodings = [codec, 'utf-8', 'utf-8-sig', 'cp932', 'shift_jis', 'euc_jp', 'iso2022_jp']
        
        for encoding in encodings:
            try:
                with open(subtitle_address, 'rb') as file:
                    data = file.read()
                    try:
                        decoded_data = data.decode(encoding)
                        subtitle['codec'] = encoding  # Update codec to the one that worked
                        dialogs = re.split('\r\n\r|\n\n', decoded_data)
                        subtitle['data'] = decoded_data
                        subtitle['raw_dialogs'] = dialogs
                        self._split_dialogs(dialogs, subtitle, color, size, top, bold, preserve_svg)
                        self.subtitles.append(subtitle)
                        return  # Successfully read file, exit function
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                continue
                
        # If we get here, none of the encodings worked
        raise ValueError(f"Could not decode subtitle file {subtitle_address} with any of the supported encodings")

    def enable_svg_filtering(self, enabled=True):
        """
        Enable or disable SVG filtering.
        
        Args:
            enabled (bool): Whether to enable SVG filtering
        """
        self.svg_filter_enabled = enabled
        
    def set_remove_text_entries(self, remove=False):
        """
        Set whether to remove text entries.
        
        Args:
            remove (bool): Whether to remove text entries
        """
        self.remove_text_entries = remove

    def get_output_path(self):
        if self.output_path.endswith('/'):
            return self.output_path + self.output_name
        return self.output_path + '/' + self.output_name

    def merge(self):
        # Reset SVG timestamp tracking before merging
        self.seen_svg_timestamps = set()
        
        self.lines = []
        self.timestamps = list(set(self.timestamps))
        self.timestamps.sort()
        count = 1
        for t in self.timestamps:
            for sub in self.subtitles:
                if t in sub['dialogs'].keys():
                    line = self._encode(sub['dialogs'][t].replace('\n\n', ''))
                    if count == 1:
                        byteOfCount = self._insert_bom(
                            bytes(str(count), encoding=self.output_encoding),
                            self.output_encoding
                        )
                    else:
                        byteOfCount = '\n'.encode(
                            self.output_encoding) + bytes(str(count), encoding=self.output_encoding)
                    if sub['dialogs'][t].endswith('\n') != True:
                        sub['dialogs'][t] = sub['dialogs'][t] + '\n'
                    dialog = byteOfCount + \
                        '\n'.encode(self.output_encoding) + line
                    self.lines.append(dialog)
                    count += 1
        
        # Check if lines list is not empty before accessing its elements
        if self.lines:
            if self.lines[-1].endswith(b'\x00\n\x00'):
                self.lines[-1] = self.lines[-1][:-3] + b'\x00'
            if self.lines[-1].endswith(b'\n'):
                self.lines[-1] = self.lines[-1][:-1] + b''
        
        # Handle the case when no lines were generated (all entries were filtered out)
        if not self.lines:
            self.logger.warning("No subtitle entries remained after filtering. Creating empty output file.")
            # Create an empty file or a file with a message
            empty_content = "1\n00:00:01,000 --> 00:00:05,000\nNo subtitle entries remained after filtering.\n"
            self.lines.append(self._encode(empty_content))
        
        with open(self.get_output_path(), 'w', encoding=self.output_encoding) as output:
            output.buffer.writelines(self.lines)
            print("'%s'" % (output.name), 'created successfully.')


# How to use?
#
# m = Merger(output_name="new.srt")
# m.add('./test_srt/en.srt')
# m.add('./test_srt/fa.srt', color="yellow", codec="cp1256", top=True)
# m.merge()
