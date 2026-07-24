from ..config import OCR_BACKEND
from .base import OCRBackend
from .tesseract_backend import TesseractOCR


_registry: dict[str, type[OCRBackend]] = {
    "pytesseract": TesseractOCR,
}


def get_ocr_backend(name: str | None = None) -> OCRBackend:
    backend_name = name or OCR_BACKEND
    cls = _registry.get(backend_name)
    if cls is None:
        available = ", ".join(_registry.keys())
        raise ValueError(
            f"Unknown OCR backend '{backend_name}'. Available: {available}"
        )
    return cls()
