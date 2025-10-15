"""Alert handling."""
from __future__ import annotations

from typing import Optional

import sqlite3

from . import models

try:
    from win10toast import ToastNotifier
except Exception:  # pragma: no cover - fallback on non-Windows
    ToastNotifier = None  # type: ignore


_notifier: Optional[ToastNotifier] = None


def _get_notifier() -> Optional[ToastNotifier]:
    global _notifier
    if _notifier is None and ToastNotifier is not None:
        try:
            _notifier = ToastNotifier()
        except Exception:
            _notifier = None
    return _notifier


def toast(title: str, message: str) -> None:
    """Show a desktop toast."""
    notifier = _get_notifier()
    if notifier is None:
        print(f"[ALERTE] {title}: {message}")
        return
    notifier.show_toast(title, message, threaded=True, duration=5)


def check_due(conn: sqlite3.Connection) -> int:
    """Process pending alerts."""
    alerts = models.list_due_alerts(conn)
    for alert in alerts:
        label = "Retour" if alert["type"] == "return" else "Garantie"
        toast(
            f"{label} à traiter",
            f"{alert['title']} chez {alert['store']} (échéance {alert['due_on']})",
        )
        models.mark_alert_sent(conn, int(alert["alert_id"]))
    return len(alerts)
