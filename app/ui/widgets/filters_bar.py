"""Filters bar widget."""
from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QDateEdit, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FiltersBar(QWidget):
    """Provide search and quick filters."""

    filters_changed = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher titre, magasin ou catégorie")
        self.store_combo = QComboBox()
        self.store_combo.addItem("Tous les magasins", "")
        self.category_combo = QComboBox()
        self.category_combo.addItem("Toutes les catégories", "")
        self.period_start = QDateEdit()
        self.period_start.setCalendarPopup(True)
        self.period_start.setDisplayFormat("yyyy-MM-dd")
        self.period_end = QDateEdit()
        self.period_end.setCalendarPopup(True)
        self.period_end.setDisplayFormat("yyyy-MM-dd")
        self.return_check = QCheckBox("Retours < 7j")
        self.warranty_check = QCheckBox("Garanties < 60j")
        self.clear_btn = QPushButton("Réinitialiser")

        layout = QHBoxLayout()
        layout.addWidget(self.search, stretch=2)
        layout.addWidget(QLabel("Magasin"))
        layout.addWidget(self.store_combo)
        layout.addWidget(QLabel("Catégorie"))
        layout.addWidget(self.category_combo)
        layout.addWidget(QLabel("Du"))
        layout.addWidget(self.period_start)
        layout.addWidget(QLabel("au"))
        layout.addWidget(self.period_end)
        layout.addWidget(self.return_check)
        layout.addWidget(self.warranty_check)
        layout.addWidget(self.clear_btn)
        layout.addStretch()
        self.setLayout(layout)

        self.search.textChanged.connect(self._emit_filters)
        self.store_combo.currentIndexChanged.connect(self._emit_filters)
        self.category_combo.currentIndexChanged.connect(self._emit_filters)
        self.period_start.dateChanged.connect(self._emit_filters)
        self.period_end.dateChanged.connect(self._emit_filters)
        self.return_check.toggled.connect(self._emit_filters)
        self.warranty_check.toggled.connect(self._emit_filters)
        self.clear_btn.clicked.connect(self._clear_filters)

    def _clear_filters(self) -> None:
        self.search.clear()
        self.store_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.period_start.setDate(QDate())
        self.period_end.setDate(QDate())
        self.return_check.setChecked(False)
        self.warranty_check.setChecked(False)
        self._emit_filters()

    def set_store_options(self, stores: list[str]) -> None:
        current = self.store_combo.currentData()
        self.store_combo.blockSignals(True)
        self.store_combo.clear()
        self.store_combo.addItem("Tous les magasins", "")
        for store in sorted(set(stores)):
            self.store_combo.addItem(store, store)
        self._restore_selection(self.store_combo, current)
        self.store_combo.blockSignals(False)

    def set_category_options(self, categories: list[str]) -> None:
        current = self.category_combo.currentData()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("Toutes les catégories", "")
        for cat in sorted(set(categories)):
            self.category_combo.addItem(cat, cat)
        self._restore_selection(self.category_combo, current)
        self.category_combo.blockSignals(False)

    @staticmethod
    def _restore_selection(combo: QComboBox, value: str | None) -> None:
        if not value:
            combo.setCurrentIndex(0)
            return
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _emit_filters(self) -> None:
        filters: Dict[str, str] = {}
        if text := self.search.text().strip():
            filters["text"] = text
        store = self.store_combo.currentData()
        if store:
            filters["store"] = store
        category = self.category_combo.currentData()
        if category:
            filters["category"] = category
        if self.period_start.date().isValid():
            filters["start"] = self.period_start.date().toString("yyyy-MM-dd")
        if self.period_end.date().isValid():
            filters["end"] = self.period_end.date().toString("yyyy-MM-dd")
        if self.return_check.isChecked():
            filters["due_return"] = date.today().isoformat()
        if self.warranty_check.isChecked():
            filters["due_warranty"] = date.today().isoformat()
        self.filters_changed.emit(filters)
