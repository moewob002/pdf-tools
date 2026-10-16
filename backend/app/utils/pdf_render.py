from pathlib import Path
from typing import Iterator

from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image


def iter_page_images(pdf_path: Path, dpi: int, **kwargs) -> Iterator[Image.Image]:
    """Rasterise a PDF one page at a time so only one page bitmap is held in memory.

    Uses the same pdftoppm renderer and arguments as rendering the whole document at
    once, so the pixels are identical; only peak memory changes.
    """
    page_count = pdfinfo_from_path(str(pdf_path))["Pages"]
    for page in range(1, page_count + 1):
        yield from convert_from_path(
            str(pdf_path), dpi=dpi, first_page=page, last_page=page, **kwargs
        )
