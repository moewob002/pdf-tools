from pathlib import Path

import pytesseract
from PIL import Image

from ..errors import UserInputError
from .base import OCRBackend

LANGUAGE_UNAVAILABLE_MESSAGE = (
    "OCR could not run with the selected language. "
    "The language data may not be installed on the server."
)


def _run(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except pytesseract.TesseractError:
        raise UserInputError(LANGUAGE_UNAVAILABLE_MESSAGE, status_code=422) from None


class TesseractOCR(OCRBackend):
    def __init__(self):
        self._supported = [
            "eng", "ind", "jpn", "kor", "chi_sim", "chi_tra",
            "ara", "deu", "fra", "spa", "por", "rus",
        ]

    def extract_text(self, image_path: Path, language: str = "eng") -> str:
        img = Image.open(image_path)
        text = _run(pytesseract.image_to_string, img, lang=language)
        return text.strip()

    def extract_data(self, image_path: Path, language: str = "eng") -> list[dict]:
        img = Image.open(image_path)
        data = _run(
            pytesseract.image_to_data, img, lang=language, output_type=pytesseract.Output.DICT
        )

        words = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if not text or conf < 30:
                continue
            words.append({
                "text": text,
                "x": data["left"][i],
                "y": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })
        return words

    def get_name(self) -> str:
        return "pytesseract"

    def get_supported_languages(self) -> list[str]:
        return self._supported
