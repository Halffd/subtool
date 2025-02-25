import jaconv
import regex
from janome.tokenizer import Tokenizer, Token

class FuriganaGenerator:
    def __init__(self) -> None:
        self.__tokenizer: Tokenizer = Tokenizer()
        self.__open_tag: str = "{"
        self.__close_tag: str = "}"


    def generate(self, text: str) -> str:
        tokens: list[Token] = list(self.__tokenizer.tokenize(text=text))
        text_with_furigana: str = ""
        
        for token in tokens:
            surface: str = token.surface

            if self.__include_kanji(token=token):
                furigana: str = jaconv.kata2hira(token.reading)
                text_with_furigana += f"{surface}{self.__open_tag}{furigana}{self.__close_tag}"
            else:
                text_with_furigana += surface
        
        return text_with_furigana
    

    def __include_kanji(self, token: Token) -> bool:
        kanji_pattern: regex.Pattern[str] = regex.compile(r"\p{Script=Han}")
        
        if kanji_pattern.search(string=token.surface) == None:
            return False
        else:
            return True