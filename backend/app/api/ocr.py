from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from ..errors import UserInputError
from ..ocr.factory import get_ocr_backend
from ..services.ocr_service import extract_text_from_pdf, make_selectable_pdf
from ..utils.validation import display_name, read_pdf_upload, validate_ocr_language

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


def _validate_ocr_options(language: str, backend: str | None) -> None:
    try:
        ocr = get_ocr_backend(backend)
    except ValueError as e:
        raise UserInputError(str(e)) from None
    validate_ocr_language(language, ocr.get_supported_languages())


@router.post("/extract-text")
async def ocr_extract_text(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    backend: str | None = Form(None),
):
    _validate_ocr_options(language, backend)
    data = await read_pdf_upload(file)

    return await extract_text_from_pdf(
        data, file.filename, language=language, backend_name=backend
    )


@router.post("/make-selectable")
async def ocr_make_selectable(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    backend: str | None = Form(None),
):
    _validate_ocr_options(language, backend)
    data = await read_pdf_upload(file)

    pdf_path = await make_selectable_pdf(
        data, file.filename, language=language, backend_name=backend
    )
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"selectable_{Path(display_name(file.filename)).stem}.pdf",
    )


@router.get("/backends")
async def list_ocr_backends():
    backends = ["pytesseract"]
    default = "pytesseract"
    return {"backends": backends, "default": default}
