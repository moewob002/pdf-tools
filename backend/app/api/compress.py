from fastapi import APIRouter, File, Form, UploadFile

from ..errors import UserInputError
from ..services.compress_service import compress_pdf
from ..utils.processing import run_processing
from ..utils.responses import job_file_response
from ..utils.validation import display_name, read_pdf_upload

router = APIRouter(prefix="/api/compress", tags=["compress"])


@router.post("")
async def compress_pdf_endpoint(
    file: UploadFile = File(...),
    quality: str = Form("medium"),
):
    if quality not in ("extreme", "low", "medium", "high"):
        raise UserInputError("Quality must be 'extreme', 'low', 'medium', or 'high'")

    data = await read_pdf_upload(file)

    pdf_path, stats = await run_processing(compress_pdf, data, file.filename, quality)
    return job_file_response(
        pdf_path,
        media_type="application/pdf",
        filename=f"compressed_{display_name(file.filename)}",
        headers={
            "X-Original-Size": str(stats["original_size"]),
            "X-Compressed-Size": str(stats["compressed_size"]),
            "X-Reduction-Percent": str(stats["reduction_percent"]),
            "X-Images-Compressed": str(stats["images_compressed"]),
            "X-Total-Images": str(stats["total_images"]),
            "X-Engine": stats.get("engine", "unknown"),
        },
    )
