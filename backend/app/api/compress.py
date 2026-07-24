from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from ..services.compress_service import compress_pdf
from ..config import MAX_FILE_SIZE

router = APIRouter(prefix="/api/compress", tags=["compress"])


@router.post("")
async def compress_pdf_endpoint(
    file: UploadFile = File(...),
    quality: str = Form("medium"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    if quality not in ("extreme", "low", "medium", "high"):
        raise HTTPException(400, "Quality must be 'extreme', 'low', 'medium', or 'high'")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 50MB)")

    pdf_path, stats = await compress_pdf(data, file.filename, quality)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"compressed_{file.filename}",
        headers={
            "X-Original-Size": str(stats["original_size"]),
            "X-Compressed-Size": str(stats["compressed_size"]),
            "X-Reduction-Percent": str(stats["reduction_percent"]),
            "X-Images-Compressed": str(stats["images_compressed"]),
            "X-Total-Images": str(stats["total_images"]),
            "X-Engine": stats.get("engine", "unknown"),
        },
    )
