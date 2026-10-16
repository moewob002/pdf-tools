import io
import zipfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from ..errors import UserInputError
from ..utils.file_utils import save_upload, temp_job
from ..utils.validation import parse_page_ranges


async def split_pdf(file_bytes: bytes, filename: str, page_ranges: str) -> Path:
    with temp_job("split") as job_dir:
        pdf_path = save_upload(file_bytes, filename, job_dir)

        reader = PdfReader(str(pdf_path))
        total = len(reader.pages)
        indices = parse_page_ranges(page_ranges, total)

        if not indices:
            raise UserInputError(f"No valid pages selected. This PDF has {total} page(s).")

        zip_path = job_dir / "split_output.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx in indices:
                writer = PdfWriter()
                writer.add_page(reader.pages[idx])
                buf = io.BytesIO()
                writer.write(buf)
                buf.seek(0)
                zf.writestr(f"page_{idx + 1}.pdf", buf.read())

        return zip_path


async def merge_pdfs(files: list[tuple[bytes, str]]) -> Path:
    with temp_job("merge") as job_dir:
        writer = PdfWriter()

        for file_bytes, filename in files:
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                writer.add_page(page)

        output_path = job_dir / "merged.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path


async def merge_custom_pages(
    files: list[tuple[bytes, str]],
    page_order: list[dict],
) -> Path:
    """Merge specific pages from files in a custom order.
    page_order: [{"file_index": 0, "page": 1}, {"file_index": 1, "page": 3}, ...]
    page numbers are 1-indexed.
    """
    with temp_job("merge") as job_dir:
        readers = []
        for file_bytes, filename in files:
            readers.append(PdfReader(io.BytesIO(file_bytes)))

        writer = PdfWriter()
        for item in page_order:
            file_idx = item["file_index"]
            page_num = item["page"]  # 1-indexed
            if 0 <= file_idx < len(readers):
                reader = readers[file_idx]
                if 1 <= page_num <= len(reader.pages):
                    writer.add_page(reader.pages[page_num - 1])

        output_path = job_dir / "merged.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path


async def delete_pages(file_bytes: bytes, filename: str, page_ranges: str) -> Path:
    with temp_job("delete") as job_dir:
        pdf_path = save_upload(file_bytes, filename, job_dir)

        reader = PdfReader(str(pdf_path))
        total = len(reader.pages)
        remove_indices = set(parse_page_ranges(page_ranges, total))

        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i not in remove_indices:
                writer.add_page(page)

        # Fixed internal name: user input never becomes part of a server path.
        output_path = job_dir / "removed_pages.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path


async def get_pdf_info(file_bytes: bytes) -> dict:
    reader = PdfReader(io.BytesIO(file_bytes))
    return {
        "total_pages": len(reader.pages),
        "metadata": reader.metadata,
    }
