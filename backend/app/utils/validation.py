"""Shared request validation. Every check raises UserInputError with a message safe to show."""
import io
import json
import re
from pathlib import Path

from fastapi import UploadFile
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError

from ..config import MAX_FILE_SIZE
from ..errors import (
    ENCRYPTED_PDF_MESSAGE,
    INVALID_IMAGE_MESSAGE,
    INVALID_PDF_MESSAGE,
    UserInputError,
)

PDF_EXTENSIONS = (".pdf",)
DOCX_EXTENSIONS = (".docx",)
IMAGE_MIME_PREFIXES = ("image/png", "image/jpeg", "image/tiff", "image/bmp")

MIN_DPI = 36
MAX_DPI = 600

_RANGE_PART = re.compile(r"^\s*(\d+)\s*(?:-\s*(\d+)\s*)?$")
_LANGUAGE_CODE = re.compile(r"^[a-z_]+$")


def display_name(filename: str | None) -> str:
    """Base name of a client-supplied filename, without any directory parts."""
    return Path((filename or "").replace("\\", "/")).name or "file"


def _too_large_message(name: str) -> str:
    return f"'{name}' is too large (max {MAX_FILE_SIZE // (1024 * 1024)}MB)."


async def read_upload(file: UploadFile, extensions: tuple[str, ...], kind: str) -> bytes:
    """Check name and size of an upload and return its bytes."""
    name = display_name(file.filename)
    if not name.lower().endswith(extensions):
        raise UserInputError(f"'{name}' is not a {kind}.")
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise UserInputError(_too_large_message(name), status_code=413)
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise UserInputError(_too_large_message(name), status_code=413)
    if not data:
        raise UserInputError(f"'{name}' is empty.")
    return data


async def read_pdf_upload(file: UploadFile) -> bytes:
    data = await read_upload(file, PDF_EXTENSIONS, "PDF file")
    ensure_readable_pdf(data)
    return data


async def read_image_upload(file: UploadFile) -> bytes:
    name = display_name(file.filename)
    if not (file.content_type or "").startswith(IMAGE_MIME_PREFIXES):
        raise UserInputError(f"'{name}' is not a supported image type (PNG, JPG, TIFF or BMP).")
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise UserInputError(_too_large_message(name), status_code=413)
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise UserInputError(_too_large_message(name), status_code=413)
    ensure_readable_image(data)
    return data


def ensure_readable_pdf(data: bytes) -> int:
    """Parse the PDF far enough to know it can be processed; return its page count."""
    try:
        page_count = len(PdfReader(io.BytesIO(data)).pages)
    except FileNotDecryptedError:
        raise UserInputError(ENCRYPTED_PDF_MESSAGE) from None
    except Exception:
        # pypdf raises a variety of exception types on malformed input.
        raise UserInputError(INVALID_PDF_MESSAGE) from None
    if page_count == 0:
        raise UserInputError("This PDF has no pages.")
    return page_count


def ensure_readable_image(data: bytes) -> None:
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
    except Image.DecompressionBombError:
        raise UserInputError("The image dimensions are too large to process.") from None
    except Exception:
        raise UserInputError(INVALID_IMAGE_MESSAGE) from None


def validate_dpi(dpi: int) -> int:
    if not MIN_DPI <= dpi <= MAX_DPI:
        raise UserInputError(f"DPI must be between {MIN_DPI} and {MAX_DPI}.")
    return dpi


def parse_page_ranges(ranges_str: str, total_pages: int) -> list[int]:
    """Parse "1-3,5,7-9" into sorted 0-based indices; pages beyond the document are ignored."""
    pages = set()
    for part in ranges_str.split(","):
        if not part.strip():
            continue
        match = _RANGE_PART.match(part)
        if not match:
            raise UserInputError(
                f"Invalid page range '{part.strip()}'. Use numbers and ranges like 1-3,5."
            )
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        for p in range(max(start, 1), min(end, total_pages) + 1):
            pages.add(p - 1)
    return sorted(pages)


def parse_page_order(page_order: str) -> list[dict]:
    """Validate the merge-custom JSON: a non-empty list of {file_index:int, page:int}."""
    try:
        order = json.loads(page_order)
    except json.JSONDecodeError:
        raise UserInputError("Invalid page_order: not valid JSON.") from None
    if not isinstance(order, list) or not order:
        raise UserInputError("Invalid page_order: must be a non-empty array.")
    for item in order:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), int) and not isinstance(item.get(key), bool)
            for key in ("file_index", "page")
        ):
            raise UserInputError(
                "Invalid page_order: each item needs integer file_index and page."
            )
    return order


def validate_ocr_language(language: str, supported: list[str]) -> str:
    """Accept a Tesseract language code or a '+'-joined combination of supported codes."""
    codes = language.split("+")
    if not all(_LANGUAGE_CODE.match(code) and code in supported for code in codes):
        raise UserInputError(
            f"Unsupported OCR language '{language}'. Supported: {', '.join(supported)}."
        )
    return language
