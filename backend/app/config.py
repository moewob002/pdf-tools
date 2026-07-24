import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

OCR_BACKEND = os.getenv("OCR_BACKEND", "pytesseract")
OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "eng").split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", 1800))
FILE_TTL = int(os.getenv("FILE_TTL", 86400))

SUPPORTED_PDF_MIME = "application/pdf"
SUPPORTED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/tiff", "image/bmp"}
SUPPORTED_DOC_MIMES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
