"""Item table model and view."""
from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QHeaderView, QTableView


class ItemTableModel(QAbstractTableModel):
    """Model for purchase entries."""

    headers = [
        "Nom",
        "Magasin",
        "Catégorie",
        "Montant",
        "Achat",
        "Retour",
        "Garantie",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._items: List[Dict[str, object]] = []

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object:  # type: ignore[override]
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        item = self._items[index.row()]
        column_key = [
            "title",
            "store",
            "category",
            "total_amount",
            "purchase_date",
            "return_until",
            "warranty_until",
        ][index.column()]
        if role == Qt.DisplayRole:
            value = item.get(column_key, "")
            if column_key == "total_amount" and isinstance(value, (int, float)):
                return f"{value:.2f} €"
            return value
        if role == Qt.UserRole:
            return item
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> object:  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers[section]
        return section + 1

    def set_items(self, items: List[Dict[str, object]]) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def item_at(self, row: int) -> Optional[Dict[str, object]]:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def find_row_by_id(self, item_id: int) -> int:
        for idx, item in enumerate(self._items):
            if int(item.get("id", -1)) == item_id:
                return idx
        return -1


class ItemTable(QTableView):
    """Table view helper."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
