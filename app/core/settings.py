"""User settings management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from . import utils


SETTINGS_FILE = utils.app_data_dir() / "settings.json"


@dataclass
class UserSettings:
    """User preferences."""

    theme: str = "light"
    return_days: int = 14
    warranty_months: int = 24
    last_opened: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "return_days": self.return_days,
            "warranty_months": self.warranty_months,
            "last_opened": self.last_opened,
        }


def load_settings(path: Path | None = None) -> UserSettings:
    """Load settings from disk."""
    target = path or SETTINGS_FILE
    data = utils.read_json(target, {})
    settings = UserSettings()
    settings.theme = data.get("theme", settings.theme)
    settings.return_days = int(data.get("return_days", settings.return_days))
    settings.warranty_months = int(data.get("warranty_months", settings.warranty_months))
    settings.last_opened = data.get("last_opened")
    return settings


def save_settings(settings: UserSettings, path: Path | None = None) -> None:
    """Persist settings."""
    target = path or SETTINGS_FILE
    utils.write_json(target, settings.as_dict())
