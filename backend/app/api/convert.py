from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from ..services.convert_service import (
    pdf_to_images,
    images_to_pdf,
    pdf_to_word,
    word_to_pdf,
)
from ..utils.validation import (
    DOCX_EXTENSIONS,
    display_name,
    read_image_upload,
    read_pdf_upload,
    read_upload,
    validate_dpi,
)

router = APIRouter(prefix="/api/convert", tags=["convert"])


@router.post("/pdf-to-image")
async def convert_pdf_to_image(
    file: UploadFile = File(...),
    format: str = Form("png"),
    dpi: int = Form(200),
):
    validate_dpi(dpi)
    data = await read_pdf_upload(file)
    zip_path = await pdf_to_images(data, file.filename, fmt=format, dpi=dpi)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{Path(display_name(file.filename)).stem}_images.zip",
    )


@router.post("/image-to-pdf")
async def convert_image_to_pdf(
    files: list[UploadFile] = File(...),
):
    file_data = []
    for f in files:
        data = await read_image_upload(f)
        file_data.append((data, f.filename))

    pdf_path = await images_to_pdf(file_data)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="converted.pdf",
    )


@router.post("/pdf-to-word")
async def convert_pdf_to_word(
    file: UploadFile = File(...),
):
    data = await read_pdf_upload(file)
    docx_path = await pdf_to_word(data, file.filename)
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{Path(display_name(file.filename)).stem}.docx",
    )


@router.post("/word-to-pdf")
async def convert_word_to_pdf(
    file: UploadFile = File(...),
):
    data = await read_upload(file, DOCX_EXTENSIONS, "Word document (.docx)")
    pdf_path = await word_to_pdf(data, file.filename)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{Path(display_name(file.filename)).stem}.pdf",
    )
