from src.utils.ass_converter import create_ass_from_srt
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Try to convert it
try:
    result = create_ass_from_srt(
        'test_subs/test2.srt',
        auto_generate_furigana=False,
        advanced_styling=True
    )
    print(f"Conversion result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 