#!/usr/bin/env python
# author: Iraj Jelodari

import datetime
import codecs
import re

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

    def _set_subtitle_style(self, subtitle, color=None, size=None):
        """
        Apply style (color and size) to subtitle text
        
        Args:
            subtitle (str): The subtitle text
            color (str): Color in HTML format (#RRGGBB) or color name
            size (int): Font size in pixels
            
        Returns:
            str: Styled subtitle text with font tags
        """
        # Split text into lines and process each line
        lines = subtitle.strip().split('\n')
        styled_lines = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Create opening font tag with both size and color if specified
            font_attrs = []
            if size is not None:  # Check for None specifically since 0 is a valid size
                font_attrs.append(f'size="{size}"')
            if color:
                font_attrs.append(f'color="{color}"')
                
            if font_attrs:
                # Combine all font attributes into a single font tag
                font_tag = f'<font {" ".join(font_attrs)}>'
                styled_lines.append(f'{font_tag}{line.strip()}</font>')
            else:
                styled_lines.append(line.strip())
        
        # Join lines with newlines and add final newline
        return '\n'.join(styled_lines) + '\n'

    def _split_dialogs(self, dialogs, subtitle, color=None, size=None, top=False):
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
                
                # Apply style (color and size) to text
                text = self._set_subtitle_style(text, color, size)
                
                # Add position if needed
                if top:
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

    def add(self, subtitle_address, codec="utf-8", color=WHITE, size=None, top=False, time_offset=0):
        """
        Add a subtitle file to be merged
        
        Args:
            subtitle_address (str): Path to subtitle file
            codec (str): Character encoding of the subtitle file
            color (str): Hex color code for the subtitle text
            size (int): Font size in pixels
            top (bool): Whether to position subtitle at top of screen
            time_offset (int): Time offset in milliseconds
        """
        subtitle = {
            'address': subtitle_address,
            'codec': codec,
            'color': color,
            'size': size,
            'dialogs': {}
        }
        with open(subtitle_address, 'r') as file:
            data = file.buffer.read().decode(codec)
            dialogs = re.split('\r\n\r|\n\n', data)
            subtitle['data'] = data
            subtitle['raw_dialogs'] = dialogs
            self._split_dialogs(dialogs, subtitle, color, size, top)
            self.subtitles.append(subtitle)

    def get_output_path(self):
        if self.output_path.endswith('/'):
            return self.output_path + self.output_name
        return self.output_path + '/' + self.output_name

    def merge(self):
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
        if self.lines[-1].endswith(b'\x00\n\x00'):
            self.lines[-1] = self.lines[-1][:-3] + b'\x00'
        if self.lines[-1].endswith(b'\n'):
            self.lines[-1] = self.lines[-1][:-1] + b''
        with open(self.get_output_path(), 'w', encoding=self.output_encoding) as output:
            output.buffer.writelines(self.lines)
            print("'%s'" % (output.name), 'created successfully.')


# How to use?
#
# m = Merger(output_name="new.srt")
# m.add('./test_srt/en.srt')
# m.add('./test_srt/fa.srt', color="yellow", codec="cp1256", top=True)
# m.merge()
