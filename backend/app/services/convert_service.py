import io
import zipfile
from pathlib import Path

from PIL import Image
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter

from ..utils.file_utils import create_temp_dir, save_upload


async def pdf_to_images(file_bytes: bytes, filename: str, fmt: str = "png", dpi: int = 200) -> Path:
    job_dir = create_temp_dir("convert")
    pdf_path = save_upload(file_bytes, filename, job_dir)

    images = convert_from_bytes(pdf_path.read_bytes(), dpi=dpi)
    output_dir = job_dir / "output"
    output_dir.mkdir(exist_ok=True)

    ext = fmt.lower()
    fmt_map = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "tiff": "TIFF", "bmp": "BMP"}
    pillow_fmt = fmt_map.get(ext, "PNG")
    if ext not in fmt_map:
        ext = "png"

    saved = []
    for i, img in enumerate(images):
        out_path = output_dir / f"page_{i + 1}.{ext}"
        img.save(out_path, pillow_fmt)
        saved.append(out_path)

    zip_path = job_dir / "output.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in saved:
            zf.write(p, p.name)

    return zip_path


async def images_to_pdf(files: list[tuple[bytes, str]], job_dir: Path | None = None) -> Path:
    job_dir = job_dir or create_temp_dir("convert")
    writer = PdfWriter()

    for file_bytes, filename in files:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode == "RGBA":
            img = img.convert("RGB")

        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="PDF")
        buf.seek(0)

        reader = PdfReader(buf)
        for page in reader.pages:
            writer.add_page(page)

    output_path = job_dir / "converted.pdf"
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


async def pdf_to_word(file_bytes: bytes, filename: str) -> Path:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    job_dir = create_temp_dir("convert")
    pdf_path = save_upload(file_bytes, filename, job_dir)

    reader = PdfReader(str(pdf_path))
    doc = Document()

    style = doc.styles["Normal"]
    style.font.size = Pt(11)

    has_text = False
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()

        if text:
            has_text = True
            for line in text.split("\n"):
                line = line.strip()
                if line:
                    doc.add_paragraph(line)
        else:
            images = convert_from_bytes(
                page.extract_image_bytes() if hasattr(page, "extract_image_bytes") else b"",
                dpi=200,
            ) if False else None

            if not images:
                try:
                    page_bytes = io.BytesIO()
                    single_writer = PdfWriter()
                    single_writer.add_page(page)
                    single_writer.write(page_bytes)
                    page_bytes.seek(0)
                    images = convert_from_bytes(page_bytes.read(), dpi=200)
                except Exception:
                    images = []

            if images:
                img_path = job_dir / f"page_{i + 1}.png"
                images[0].save(img_path, "PNG")
                doc.add_picture(str(img_path), width=Inches(6))

        if i < len(reader.pages) - 1:
            doc.add_page_break()

    if not has_text:
        doc = Document()
        for i, page in enumerate(reader.pages):
            try:
                page_bytes = io.BytesIO()
                single_writer = PdfWriter()
                single_writer.add_page(page)
                single_writer.write(page_bytes)
                page_bytes.seek(0)
                images = convert_from_bytes(page_bytes.read(), dpi=200)
                if images:
                    img_path = job_dir / f"page_{i + 1}.png"
                    images[0].save(img_path, "PNG")
                    doc.add_picture(str(img_path), width=Inches(6))
                    if i < len(reader.pages) - 1:
                        doc.add_page_break()
            except Exception:
                pass

    output_path = job_dir / f"{Path(filename).stem}.docx"
    doc.save(str(output_path))
    return output_path


async def word_to_pdf(file_bytes: bytes, filename: str) -> Path:
    from docx import Document

    job_dir = create_temp_dir("convert")
    docx_path = save_upload(file_bytes, filename, job_dir)

    doc = Document(str(docx_path))

    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    has_images = False
    tmp_dir = job_dir / "tmp_img"
    tmp_dir.mkdir(exist_ok=True)

    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            img_data = rel.target_part.blob
            ext = Path(rel.target_part.partname).suffix
            img_path = tmp_dir / f"img_{len(images)}{ext}"
            img_path.write_bytes(img_data)
            images.append(img_path)

    if images:
        return await images_to_pdf(
            [(img_path.read_bytes(), img_path.name) for img_path in images],
            job_dir,
        )

    for para in doc.paragraphs:
        if para.text.strip():
            if pdf.pages_count == 0 or pdf.get_y() > 270:
                pdf.add_page()
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 10, para.text)

    if pdf.pages_count == 0:
        pdf.add_page()

    output_path = job_dir / f"{Path(filename).stem}.pdf"
    pdf.output(str(output_path))
    return output_path
