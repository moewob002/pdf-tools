import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from ..config import TEMP_DIR, FILE_TTL


def create_temp_dir(prefix: str = "job") -> Path:
    job_id = f"{prefix}_{uuid.uuid4().hex[:12]}"
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def save_upload(file_bytes: bytes, filename: str, dest_dir: Path) -> Path:
    ext = Path(filename).suffix or ".pdf"
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


def get_file_size(file_bytes: bytes) -> int:
    return len(file_bytes)
