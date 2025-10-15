"""Entry point for ProofPal Desktop."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon, QPalette, QColor
from PySide6.QtWidgets import QApplication

from .assets.icon_png import ensure_icon
from .core import db, settings, utils
from .ui.main_window import MainWindow


def apply_theme(app: QApplication, user_settings: settings.UserSettings) -> None:
    """Apply Fusion theme and stylesheet."""
    app.setStyle("Fusion")
    palette = app.palette()
    if user_settings.theme == "dark":
        palette.setColor(QPalette.Window, QColor(30, 32, 43))
        palette.setColor(QPalette.WindowText, QColor("white"))
        palette.setColor(QPalette.Base, QColor(45, 47, 62))
        palette.setColor(QPalette.AlternateBase, QColor(50, 52, 70))
        palette.setColor(QPalette.Text, QColor("white"))
        palette.setColor(QPalette.Button, QColor(45, 47, 62))
    app.setPalette(palette)
    style_path = Path(__file__).resolve().parent / "assets" / "style.qss"
    app.setStyleSheet(style_path.read_text(encoding="utf-8"))


def main() -> int:
    """Start the Qt application."""
    utils.app_data_dir()
    utils.files_dir()
    db.init_db()
    user_settings = settings.load_settings()
    app = QApplication(sys.argv)
    icon_path = ensure_icon()
    app.setWindowIcon(QIcon(str(icon_path)))
    apply_theme(app, user_settings)
    window = MainWindow(user_settings)
    window.show()

    timer = QTimer()
    timer.setInterval(60_000)
    timer.timeout.connect(window.notify_due_alerts)
    timer.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
