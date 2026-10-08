import secrets
import string
import uuid
import qrcode
import io
import base64
from pathlib import Path
from qrcode.image.svg import SvgPathImage
from app.utils.files import get_unique_filename, get_result_filepath

class GeneratorService:
    @staticmethod
    def generate_password(
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_symbols: bool = True
    ) -> str:
        chars = ""
        if include_uppercase:
            chars += string.ascii_uppercase
        if include_lowercase:
            chars += string.ascii_lowercase
        if include_numbers:
            chars += string.digits
        if include_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
        if not chars:
            chars = string.ascii_letters + string.digits
            
        # Use Python's cryptographically secure secrets module
        return "".join(secrets.choice(chars) for _ in range(max(4, min(128, length))))

    @staticmethod
    def generate_uuids(count: int = 1, version: str = "v4") -> list[str]:
        count = max(1, min(100, count))
        results = []
        for _ in range(count):
            results.append(str(uuid.uuid4()))
        return results

    @staticmethod
    def generate_qr_code(data: str, size: int = 10, error_correction: str = "M", format: str = "png") -> str:
        ec_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }
        ec_level = ec_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
        
        qr = qrcode.QRCode(
            version=None,
            error_correction=ec_level,
            box_size=max(2, min(30, size)),
            border=3,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        if format.lower() == "svg":
            img = qr.make_image(image_factory=SvgPathImage)
            buffer = io.BytesIO()
            img.save(buffer)
            svg_str = buffer.getvalue().decode('utf-8')
            return f"data:image/svg+xml;utf8,{svg_str}"
        else:
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{img_b64}"

    @staticmethod
    def generate_random_string(length: int = 16, charset: str = "alphanumeric") -> str:
        if charset == "numeric":
            pool = string.digits
        elif charset == "alphabetic":
            pool = string.ascii_letters
        elif charset == "hex":
            pool = string.hexdigits.lower()
        else:
            pool = string.ascii_letters + string.digits
            
        return "".join(secrets.choice(pool) for _ in range(max(1, min(500, length))))

    @staticmethod
    def generate_color_palette(count: int = 5) -> list[dict]:
        palettes = []
        for _ in range(max(1, min(20, count))):
            r, g, b = secrets.randbelow(256), secrets.randbelow(256), secrets.randbelow(256)
            hex_code = f"#{r:02X}{g:02X}{b:02X}"
            palettes.append({
                "hex": hex_code,
                "rgb": f"rgb({r}, {g}, {b})",
                "hsl": f"hsl({int((r/255)*360)}, 70%, 50%)"
            })
        return palettes
