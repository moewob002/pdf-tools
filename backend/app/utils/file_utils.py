import logging
import re
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

from ..config import FILE_TTL, TEMP_DIR

logger = logging.getLogger(__name__)

_SAFE_SUFFIX = re.compile(r"^\.[A-Za-z0-9]{1,8}$")


def create_temp_dir(prefix: str = "job") -> Path:
    job_id = f"{prefix}_{uuid.uuid4().hex[:12]}"
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


@contextmanager
def temp_job(prefix: str = "job") -> Iterator[Path]:
    """Create a job directory that is removed if processing fails.

    On success the directory is kept so the route can stream the result; the route
    then removes it after the response with remove_job_dir().
    """
    job_dir = create_temp_dir(prefix)
    try:
        yield job_dir
    except BaseException:
        remove_job_dir(job_dir)
        raise


def remove_job_dir(job_dir: Path) -> None:
    """Delete a job directory, refusing anything that is not a direct child of TEMP_DIR."""
    job_dir = Path(job_dir)
    if job_dir.resolve().parent != TEMP_DIR.resolve():
        logger.warning("Refusing to remove non-job directory %s", job_dir)
        return
    shutil.rmtree(job_dir, ignore_errors=True)


def save_upload(file_bytes: bytes, filename: str, dest_dir: Path) -> Path:
    ext = Path(filename).suffix
    if not _SAFE_SUFFIX.match(ext):
        ext = ".pdf"
    safe_name = f"{uuid.uuid4().hex[:8]}{ext}"
    file_path = dest_dir / safe_name
    file_path.write_bytes(file_bytes)
    return file_path


def cleanup_old_files():
    now = datetime.now()
    cutoff = now - timedelta(seconds=FILE_TTL)
    if not TEMP_DIR.exists():
        return
    for item in TEMP_DIR.iterdir():
        if item.is_dir():
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(item, ignore_errors=True)
        elif item.is_file():
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if mtime < cutoff:
                item.unlink(missing_ok=True)
