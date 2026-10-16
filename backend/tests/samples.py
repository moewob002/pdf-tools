"""Sample documents generated in memory for tests (no binary fixtures in the repo)."""
import io
import shutil

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

HAS_POPPLER = shutil.which("pdftoppm") is not None and shutil.which("pdfinfo") is not None
HAS_GHOSTSCRIPT = shutil.which("gs") is not None
HAS_TESSERACT = shutil.which("tesseract") is not None


def text_pdf(pages: int = 3) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for i in range(pages):
        c.setFont("Helvetica", 24)
        c.drawString(72, 750, f"Sample page {i + 1} of {pages}")
        c.showPage()
    c.save()
    return buf.getvalue()


def encrypted_pdf(user_password: str = "secret") -> bytes:
    writer = PdfWriter()
    for page in PdfReader(io.BytesIO(text_pdf(2))).pages:
        writer.add_page(page)
    writer.encrypt(user_password, algorithm="AES-256")
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def scanned_pdf() -> bytes:
    img = Image.new("RGB", (1240, 400), "white")
    ImageDraw.Draw(img).text((50, 150), "HELLO OCR", fill="black", font_size=96)
    buf = io.BytesIO()
    img.save(buf, "PDF", resolution=150)
    return buf.getvalue()


def png(color=(30, 120, 220), size=(64, 48)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def docx(*paragraphs: str) -> bytes:
    from docx import Document

    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def page_count(pdf_bytes: bytes) -> int:
    return len(PdfReader(io.BytesIO(pdf_bytes)).pages)


GARBAGE = bytes(range(256)) * 16
