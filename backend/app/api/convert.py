import io
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from ..services.convert_service import (
    pdf_to_images,
    images_to_pdf,
    pdf_to_word,
    word_to_pdf,
)
from ..config import MAX_FILE_SIZE

router = APIRouter(prefix="/api/convert", tags=["convert"])


async def _validate_file(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    return data


@router.post("/pdf-to-image")
async def convert_pdf_to_image(
    file: UploadFile = File(...),
    format: str = Form("png"),
    dpi: int = Form(200),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    data = await _validate_file(file)
    zip_path = await pdf_to_images(data, file.filename, fmt=format, dpi=dpi)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{Path(file.filename).stem}_images.zip",
    )


@router.post("/image-to-pdf")
async def convert_image_to_pdf(
    files: list[UploadFile] = File(...),
):
    for f in files:
        if not any(
            f.content_type and f.content_type.startswith(t)
            for t in ("image/png", "image/jpeg", "image/tiff", "image/bmp")
        ):
            raise HTTPException(400, f"{f.filename} is not a supported image type")

    file_data = []
    for f in files:
        data = await _validate_file(f)
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
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    data = await _validate_file(file)
    docx_path = await pdf_to_word(data, file.filename)
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{Path(file.filename).stem}.docx",
    )


@router.post("/word-to-pdf")
async def convert_word_to_pdf(
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith((".docx", ".doc")):
        raise HTTPException(400, "File must be a Word document")

    data = await _validate_file(file)
    pdf_path = await word_to_pdf(data, file.filename)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{Path(file.filename).stem}.pdf",
    )
