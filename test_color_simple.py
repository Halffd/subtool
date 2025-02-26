#!/usr/bin/env python3
import re

# Sample text with color tags
text = '<font color="blue">青い</font>空(そら)と<font color="red">赤い</font>夕日(ゆうひ)'

# Color mapping
COLOR_MAP = {
    "red": "&H0000FF&",
    "blue": "&HFF0000&",
    "green": "&H00FF00&",
    "yellow": "&H00FFFF&",
    "cyan": "&HFFFF00&",
    "magenta": "&HFF00FF&",
    "white": "&HFFFFFF&",
    "black": "&H000000&",
    "lightblue": "&H008AE6&",
    "darkblue": "&H0000E6&",
    "purple": "&HE600AC&",
    "orange": "&HE65C00&",
    "darkgreen": "&H2B8000&"
}

print(f"Original text: {text}")

# Process color tags
if "<font color=" in text:
    print("Found color tags in text")
    # Extract all color tags
    color_matches = list(re.finditer(r'<font color="([^"]+)">(.*?)</font>', text))
    
    # Process each match from end to beginning to avoid index issues
    processed_text = text
    for match in reversed(color_matches):
        color = match.group(1)
        content = match.group(2)
        print(f"Processing color tag: color={color}, content={content}")
        
        # Convert HTML color to ASS color
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
        else:
            # Map common color names to ASS colors
            ass_color = COLOR_MAP.get(color.lower(), "&H00FFFFFF&")
        
        print(f"Converted color to ASS format: {ass_color}")
        
        # Create ASS color tag
        color_tag_start = f"{{\\c{ass_color}}}"
        color_tag_end = "{\\c}"
        
        # Replace the HTML tag with ASS color tag
        processed_text = processed_text[:match.start()] + color_tag_start + content + color_tag_end + processed_text[match.end():]
        print(f"Processed text with color tags: {processed_text}")

    print(f"\nFinal processed text: {processed_text}")
else:
    print("No color tags found in text") 