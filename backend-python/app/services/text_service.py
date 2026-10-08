import re
import base64
import urllib.parse

class TextService:
    @staticmethod
    def word_count(text: str) -> dict:
        words = re.findall(r'\b\w+\b', text)
        chars_with_spaces = len(text)
        chars_no_spaces = len(re.sub(r'\s+', '', text))
        lines = len(text.splitlines()) if text else 0
        sentences = len(re.findall(r'[^.!?]+[.!?]', text)) or (1 if words else 0)
        paragraphs = len([p for p in text.split('\n\n') if p.strip()])
        reading_time_minutes = round(len(words) / 200, 1) # 200 wpm
        
        return {
            "words": len(words),
            "characters": chars_with_spaces,
            "charactersNoSpaces": chars_no_spaces,
            "lines": lines,
            "sentences": sentences,
            "paragraphs": paragraphs,
            "readingTimeMinutes": reading_time_minutes
        }

    @staticmethod
    def case_convert(text: str, target_case: str) -> str:
        if not text:
            return ""
            
        words = re.findall(r'[A-Za-z0-9]+', text)
        
        if target_case == "upper":
            return text.upper()
        elif target_case == "lower":
            return text.lower()
        elif target_case == "title":
            return text.title()
        elif target_case == "camel":
            if not words: return ""
            return words[0].lower() + "".join(w.capitalize() for w in words[1:])
        elif target_case == "snake":
            return "_".join(w.lower() for w in words)
        elif target_case == "kebab":
            return "-".join(w.lower() for w in words)
        elif target_case == "pascal":
            return "".join(w.capitalize() for w in words)
        return text

    @staticmethod
    def clean_text(text: str, remove_duplicates: bool = True, trim_lines: bool = True, remove_empty: bool = True) -> str:
        lines = text.splitlines()
        
        if trim_lines:
            lines = [l.strip() for l in lines]
            
        if remove_empty:
            lines = [l for l in lines if l]
            
        if remove_duplicates:
            seen = set()
            unique_lines = []
            for l in lines:
                if l not in seen:
                    seen.add(l)
                    unique_lines.append(l)
            lines = unique_lines
            
        return "\n".join(lines)

    @staticmethod
    def base64_encode(text: str) -> str:
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    @staticmethod
    def base64_decode(text: str) -> str:
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return "Error: Invalid Base64 string."

    @staticmethod
    def url_encode(text: str) -> str:
        return urllib.parse.quote(text)

    @staticmethod
    def url_decode(text: str) -> str:
        return urllib.parse.unquote(text)
