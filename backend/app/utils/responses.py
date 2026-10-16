from pathlib import Path

from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .file_utils import remove_job_dir


def job_file_response(
    path: Path, media_type: str, filename: str, headers: dict | None = None
) -> FileResponse:
    """Stream a result file, then delete its job directory once the response is sent."""
    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
        headers=headers,
        background=BackgroundTask(remove_job_dir, Path(path).parent),
    )
