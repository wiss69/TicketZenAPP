"""Preview panel for attachments."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import fitz
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class PreviewPanel(QWidget):
    """Display attachment preview."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.label = QLabel("Sélectionnez un fichier pour l'aperçu")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumHeight(240)
        self.open_button = QPushButton("Ouvrir le fichier")
        self.open_button.setEnabled(False)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.open_button)
        self.setLayout(layout)
        self.current_path: Optional[Path] = None
        self.open_button.clicked.connect(self._open_external)

    def _open_external(self) -> None:
        if not self.current_path:
            return
        try:
            os.startfile(self.current_path)  # type: ignore[attr-defined]
        except AttributeError:
            os.system(f'xdg-open "{self.current_path}" >/dev/null 2>&1')

    def show_file(self, path: Path) -> None:
        self.current_path = path
        self.open_button.setEnabled(True)
        if path.suffix.lower() == ".pdf":
            self._show_pdf(path)
        elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}:
            self._show_image(path)
        else:
            self.label.setText(f"Impossible d'afficher {path.name}")

    def clear(self) -> None:
        self.current_path = None
        self.open_button.setEnabled(False)
        self.label.setPixmap(QPixmap())
        self.label.setText("Sélectionnez un fichier pour l'aperçu")

    def _show_image(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        target_size = self.label.size()
        if target_size.width() == 0 or target_size.height() == 0:
            target_size = self.label.sizeHint()
        self.label.setPixmap(pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _show_pdf(self, path: Path) -> None:
        doc = fitz.open(path)
        if doc.page_count == 0:
            self.label.setText("PDF vide")
            return
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888).copy()
        pixmap = QPixmap.fromImage(image)
        target_size = self.label.size()
        if target_size.width() == 0 or target_size.height() == 0:
            target_size = self.label.sizeHint()
        self.label.setPixmap(pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
