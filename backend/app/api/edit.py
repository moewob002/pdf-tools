import base64
import io

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from ..errors import UserInputError
from ..services.edit_service import split_pdf, merge_pdfs, merge_custom_pages, delete_pages, get_pdf_info
from ..utils.validation import parse_page_order, read_pdf_upload, validate_dpi

router = APIRouter(prefix="/api/edit", tags=["edit"])


@router.post("/split")
async def split_pdf_endpoint(
    file: UploadFile = File(...),
    pages: str = Form(..., description='Page ranges, e.g. "1-3,5,7-9"'),
):
    data = await read_pdf_upload(file)
    zip_path = await split_pdf(data, file.filename, pages)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="split_pages.zip",
    )


@router.post("/merge")
async def merge_pdfs_endpoint(
    files: list[UploadFile] = File(..., description="PDF files to merge in order"),
):
    if len(files) < 2:
        raise UserInputError("At least 2 PDF files required for merge")

    file_data = []
    for f in files:
        data = await read_pdf_upload(f)
        file_data.append((data, f.filename))

    pdf_path = await merge_pdfs(file_data)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="merged.pdf",
    )


@router.post("/merge-custom")
async def merge_custom_endpoint(
    files: list[UploadFile] = File(..., description="PDF files to merge"),
    page_order: str = Form(..., description='JSON array of {file_index, page} objects'),
):
    order = parse_page_order(page_order)

    file_data = []
    for f in files:
        data = await read_pdf_upload(f)
        file_data.append((data, f.filename))

    pdf_path = await merge_custom_pages(file_data, order)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="merged.pdf",
    )


@router.post("/delete-pages")
async def delete_pages_endpoint(
    file: UploadFile = File(...),
    pages: str = Form(..., description='Pages to remove, e.g. "2,4,6-8"'),
):
    data = await read_pdf_upload(file)
    pdf_path = await delete_pages(data, file.filename, pages)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="removed_pages.pdf",
    )


@router.post("/info")
async def pdf_info_endpoint(
    file: UploadFile = File(...),
):
    data = await read_pdf_upload(file)
    info = await get_pdf_info(data)
    return info


@router.post("/thumbnails")
async def pdf_thumbnails(
    file: UploadFile = File(...),
    dpi: int = Form(100),
):
    from pdf2image import convert_from_bytes

    validate_dpi(dpi)
    data = await read_pdf_upload(file)
    images = convert_from_bytes(data, dpi=dpi, fmt="JPEG")

    thumbnails = []
    for i, img in enumerate(images):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        buf.seek(0)
        thumbnails.append({
            "page": i + 1,
            "image": buf.getvalue(),
        })

    result = {
        "total_pages": len(thumbnails),
        "pages": [
            {"page": t["page"], "image": base64.b64encode(t["image"]).decode()}
            for t in thumbnails
        ],
    }
    return result
