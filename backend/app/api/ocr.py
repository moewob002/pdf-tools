from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from ..services.ocr_service import extract_text_from_pdf, make_selectable_pdf
from ..ocr.factory import get_ocr_backend
from ..config import MAX_FILE_SIZE

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/extract-text")
async def ocr_extract_text(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    backend: str | None = Form(None),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 50MB)")

    try:
        result = await extract_text_from_pdf(
            data, file.filename, language=language, backend_name=backend
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"OCR processing failed: {str(e)}")

    return result


@router.post("/make-selectable")
async def ocr_make_selectable(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    backend: str | None = Form(None),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 50MB)")

    try:
        pdf_path = await make_selectable_pdf(
            data, file.filename, language=language, backend_name=backend
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"OCR processing failed: {str(e)}")

    from pathlib import Path
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"selectable_{Path(file.filename).stem}.pdf",
    )


@router.get("/backends")
async def list_ocr_backends():
    backends = ["pytesseract"]
    default = "pytesseract"
    return {"backends": backends, "default": default}
