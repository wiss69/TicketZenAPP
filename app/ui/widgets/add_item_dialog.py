"""Dialog to add or edit an item."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QDoubleSpinBox,
    QWidget,
)

from ...core import settings as settings_module
from ...core import utils


class AddItemDialog(QDialog):
    """Dialog to capture purchase details."""

    def __init__(
        self,
        user_settings: settings_module.UserSettings,
        parent: Optional[QWidget] = None,
        existing: Optional[Dict[str, object]] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvel achat" if existing is None else "Modifier l'achat")
        self.settings = user_settings
        self.files: List[Path] = []
        self._build_ui()
        self._populate(existing)

    def _build_ui(self) -> None:
        self.title_edit = QLineEdit()
        self.store_edit = QLineEdit()
        self.category_edit = QLineEdit()
        self.purchase_date = QDateEdit()
        self.purchase_date.setCalendarPopup(True)
        self.purchase_date.setDisplayFormat("yyyy-MM-dd")
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setMaximum(1_000_000.0)
        self.amount_edit.setPrefix("€ ")
        self.amount_edit.setDecimals(2)
        self.return_date = QDateEdit()
        self.return_date.setCalendarPopup(True)
        self.return_date.setDisplayFormat("yyyy-MM-dd")
        self.warranty_date = QDateEdit()
        self.warranty_date.setCalendarPopup(True)
        self.warranty_date.setDisplayFormat("yyyy-MM-dd")
        self.notes_edit = QTextEdit()

        self.files_list = QListWidget()
        add_file_btn = QPushButton("Ajouter des pièces")
        add_file_btn.clicked.connect(self._choose_files)

        form = QFormLayout()
        form.addRow("Titre", self.title_edit)
        form.addRow("Magasin", self.store_edit)
        form.addRow("Catégorie", self.category_edit)
        form.addRow("Date d'achat", self.purchase_date)
        form.addRow("Montant", self.amount_edit)
        form.addRow("Retour jusqu'au", self.return_date)
        form.addRow("Garantie jusqu'au", self.warranty_date)
        form.addRow("Notes", self.notes_edit)

        file_layout = QVBoxLayout()
        file_layout.addWidget(add_file_btn)
        file_layout.addWidget(self.files_list)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(file_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _populate(self, existing: Optional[Dict[str, object]]) -> None:
        today = date.today()
        default_purchase = QDate(today.year, today.month, today.day)
        self.purchase_date.setDate(default_purchase)
        self.amount_edit.setValue(0.0)
        if existing:
            self.title_edit.setText(str(existing.get("title", "")))
            self.store_edit.setText(str(existing.get("store", "")))
            self.category_edit.setText(str(existing.get("category", "")))
            self.purchase_date.setDate(QDate.fromString(str(existing.get("purchase_date")), "yyyy-MM-dd"))
            self.amount_edit.setValue(float(existing.get("total_amount", 0.0)))
            self.return_date.setDate(QDate.fromString(str(existing.get("return_until")), "yyyy-MM-dd"))
            self.warranty_date.setDate(QDate.fromString(str(existing.get("warranty_until")), "yyyy-MM-dd"))
            self.notes_edit.setPlainText(str(existing.get("notes", "")))
            self.setWindowTitle("Modifier l'achat")
        else:
            purchase = today
            default_return = utils.default_return_date(purchase, self.settings.return_days)
            default_warranty = utils.default_warranty_date(purchase, self.settings.warranty_months)
            self.return_date.setDate(QDate(default_return.year, default_return.month, default_return.day))
            self.warranty_date.setDate(QDate(default_warranty.year, default_warranty.month, default_warranty.day))

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Sélectionner des pièces")
        for path_str in paths:
            path = Path(path_str)
            if path.exists() and path not in self.files:
                self.files.append(path)
                item = QListWidgetItem(path.name)
                self.files_list.addItem(item)

    def get_data(self) -> Optional[Dict[str, object]]:
        if not self.title_edit.text().strip():
            return None
        purchase = self.purchase_date.date().toPython()
        if not self.return_date.date().isValid():
            ret = utils.default_return_date(purchase, self.settings.return_days)
        else:
            ret = self.return_date.date().toPython()
        if not self.warranty_date.date().isValid():
            warranty = utils.default_warranty_date(purchase, self.settings.warranty_months)
        else:
            warranty = self.warranty_date.date().toPython()
        return {
            "title": self.title_edit.text().strip(),
            "store": self.store_edit.text().strip() or "N/A",
            "category": self.category_edit.text().strip() or "Divers",
            "purchase_date": purchase.isoformat(),
            "total_amount": float(self.amount_edit.value()),
            "return_until": ret.isoformat(),
            "warranty_until": warranty.isoformat(),
            "notes": self.notes_edit.toPlainText().strip(),
        }

    def get_files(self) -> List[Path]:
        return self.files
