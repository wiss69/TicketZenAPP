"""File storage helpers."""
from __future__ import annotations

from datetime import datetime
import mimetypes
import shutil
from pathlib import Path
from typing import Dict

from . import utils


def ensure_item_dir(item_id: int) -> Path:
    """Ensure the directory for an item exists."""
    base = utils.files_dir() / str(item_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


def compute_checksum(path: Path) -> str:
    """Compute checksum."""
    return utils.checksum_sha256(path)


def copy_file_to_item(src: Path, item_id: int) -> Dict[str, str | int | Path]:
    """Copy file to the archive directory."""
    if not src.exists():
        raise FileNotFoundError(src)
    target_dir = ensure_item_dir(item_id)
    checksum = compute_checksum(src)
    ext = src.suffix.lower()
    dest_name = f"{checksum[:16]}{ext}"
    dest = target_dir / dest_name
    if not dest.exists():
        shutil.copy2(src, dest)
    mime = mimetypes.guess_type(dest.name)[0] or "application/octet-stream"
    size = dest.stat().st_size
    return {
        "path": dest,
        "mime": mime,
        "size": size,
        "checksum": checksum,
        "uploaded_at": datetime.utcnow().isoformat(timespec="seconds"),
    }


def remove_file(path: Path) -> None:
    """Delete a stored file."""
    if path.exists():
        path.unlink()
        parent = path.parent
        try:
            parent.rmdir()
        except OSError:
            pass
