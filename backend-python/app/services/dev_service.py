import json
import time
import hashlib
import re
import html
import base64
from datetime import datetime, timezone

class DevService:
    @staticmethod
    def format_json(raw_json: str, indent: int = 2) -> dict:
        try:
            parsed = json.loads(raw_json)
            formatted = json.dumps(parsed, indent=indent)
            return {"valid": True, "formatted": formatted, "error": None}
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "formatted": raw_json,
                "error": f"Line {e.lineno}, Col {e.colno}: {e.msg}"
            }

    @staticmethod
    def convert_timestamp(ts: float) -> dict:
        # Check if milliseconds
        if ts > 1e11:
            ts_sec = ts / 1000.0
        else:
            ts_sec = ts
            
        dt_utc = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
        return {
            "epochSeconds": int(ts_sec),
            "epochMillis": int(ts_sec * 1000),
            "isoUtc": dt_utc.isoformat(),
            "readableUtc": dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    @staticmethod
    def generate_hashes(text: str) -> dict:
        b = text.encode('utf-8')
        return {
            "md5": hashlib.md5(b).hexdigest(),
            "sha1": hashlib.sha1(b).hexdigest(),
            "sha256": hashlib.sha256(b).hexdigest(),
            "sha512": hashlib.sha512(b).hexdigest(),
        }

    @staticmethod
    def test_regex(pattern: str, text: str, flags: str = "") -> dict:
        py_flags = 0
        if "i" in flags: py_flags |= re.IGNORECASE
        if "m" in flags: py_flags |= re.MULTILINE
        if "s" in flags: py_flags |= re.DOTALL
        
        try:
            regex = re.compile(pattern, py_flags)
            matches = []
            for match in regex.finditer(text):
                matches.append({
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "groups": match.groups()
                })
            return {"valid": True, "matchesCount": len(matches), "matches": matches, "error": None}
        except re.error as e:
            return {"valid": False, "matchesCount": 0, "matches": [], "error": str(e)}

    @staticmethod
    def decode_jwt(token: str) -> dict:
        """
        Safely inspects and decodes JWT header and payload without forging or verifying keys.
        """
        parts = token.strip().split('.')
        if len(parts) != 3:
            return {"valid": False, "error": "Invalid JWT format. Must contain 3 parts separated by dots."}
            
        def b64_url_decode(segment: str) -> dict:
            rem = len(segment) % 4
            if rem > 0:
                segment += '=' * (4 - rem)
            decoded_bytes = base64.urlsafe_b64decode(segment)
            return json.loads(decoded_bytes.decode('utf-8'))

        try:
            header = b64_url_decode(parts[0])
            payload = b64_url_decode(parts[1])
            return {
                "valid": True,
                "header": header,
                "payload": payload,
                "signatureHex": parts[2][:16] + "...",
                "error": None
            }
        except Exception as e:
            return {"valid": False, "error": f"Failed to decode JWT payload: {str(e)}"}

    @staticmethod
    def html_encode(text: str) -> str:
        return html.escape(text)

    @staticmethod
    def html_decode(text: str) -> str:
        return html.unescape(text)
