from pathlib import Path
import io

from ..ocr.factory import get_ocr_backend
from ..utils.file_utils import remove_job_dir, save_upload, temp_job
from ..utils.pdf_render import iter_page_images


def extract_text_from_pdf(
    file_bytes: bytes,
    filename: str,
    language: str = "eng",
    backend_name: str | None = None,
) -> dict:
    with temp_job("ocr") as job_dir:
        pdf_path = save_upload(file_bytes, filename, job_dir)

        ocr = get_ocr_backend(backend_name)
        pages_text = []
        for i, img in enumerate(iter_page_images(pdf_path, dpi=300)):
            img_path = job_dir / f"page_{i + 1}.png"
            img.save(img_path, "PNG")
            text = ocr.extract_text(img_path, language=language)
            pages_text.append({"page": i + 1, "text": text})

        full_text = "\n\n".join(p["text"] for p in pages_text)

    # The result is returned as JSON, so nothing on disk is needed any more.
    remove_job_dir(job_dir)
    return {
        "backend": ocr.get_name(),
        "language": language,
        "total_pages": len(pages_text),
        "pages": pages_text,
        "full_text": full_text,
    }


def make_selectable_pdf(
    file_bytes: bytes,
    filename: str,
    language: str = "eng",
    backend_name: str | None = None,
) -> Path:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color

    with temp_job("ocr_selectable") as job_dir:
        pdf_path = save_upload(file_bytes, filename, job_dir)

        dpi = 300
        original_reader = PdfReader(io.BytesIO(file_bytes))

        ocr = get_ocr_backend(backend_name)

        writer = PdfWriter()

        for i, img in enumerate(iter_page_images(pdf_path, dpi=dpi)):
            img_path = job_dir / f"page_{i + 1}.png"
            img.save(img_path, "PNG")

            ocr_data = ocr.extract_data(img_path, language=language)

            orig_page = original_reader.pages[i]
            orig_w = float(orig_page.mediabox.width)
            orig_h = float(orig_page.mediabox.height)

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(orig_w, orig_h))

            c._code.append("3 Tr")
            c._code.append("0 0 0 rg")
            c._code.append("0 0 0 RG")

            scale = 72 / dpi

            for word_info in ocr_data:
                x = word_info["x"] * scale
                y_top = word_info["y"] * scale
                h = word_info["height"] * scale
                text = word_info["text"]

                if not text.strip():
                    continue

                font_size = max(h * 0.8, 4)
                y_bottom = orig_h - y_top - h

                c.setFont("Helvetica", font_size)
                c.setFillColor(Color(0, 0, 0, alpha=0))
                c.setStrokeColor(Color(0, 0, 0, alpha=0))
                c.drawString(x, y_bottom, text)

            c.save()
            buf.seek(0)

            text_reader = PdfReader(buf)
            text_page = text_reader.pages[0]

            orig_page.merge_page(text_page)
            writer.add_page(orig_page)

        output_path = job_dir / "selectable.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path
