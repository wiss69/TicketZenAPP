"""Utility helpers for ProofPal."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dateutil.relativedelta import relativedelta

APP_NAME = "ProofPal"


def _local_appdata() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base)
    home = Path.home()
    return home / "AppData" / "Local"


def app_data_dir() -> Path:
    """Return and ensure the application data directory."""
    path = _local_appdata() / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """Return the database path."""
    return app_data_dir() / "proofpal.db"


def files_dir() -> Path:
    """Return and ensure the files directory."""
    path = app_data_dir() / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def documents_dir() -> Path:
    """Return and ensure the export directory."""
    base = os.getenv("USERPROFILE")
    if base:
        documents = Path(base) / "Documents" / APP_NAME
    else:
        documents = Path.home() / "Documents" / APP_NAME
    documents.mkdir(parents=True, exist_ok=True)
    return documents


def format_money(value: float) -> str:
    """Format a monetary value."""
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    return f"{amount:,.2f} €".replace(",", " ")


def parse_date(value: Any) -> Optional[date]:
    """Parse a value into date if possible."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return None


def days_until(target: date) -> int:
    """Return days until target date."""
    today = date.today()
    return (target - today).days


def default_return_date(purchase: date, days: int) -> date:
    """Compute the default return date."""
    return purchase + relativedelta(days=days)


def default_warranty_date(purchase: date, months: int) -> date:
    """Compute the default warranty date."""
    return purchase + relativedelta(months=months)


def checksum_sha256(path: Path) -> str:
    """Compute file checksum."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_json(path: Path, default: Any) -> Any:
    """Read JSON data."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    """Write JSON data."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


@dataclass
class AuditEntry:
    """Audit log entry."""

    action: str
    details_json: Dict[str, Any]
    ts: datetime
