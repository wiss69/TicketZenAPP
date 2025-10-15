"""Dashboard widget."""
from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QGridLayout, QGroupBox


class StatCard(QGroupBox):
    """Simple stat card."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class Dashboard(QWidget):
    """Dashboard summary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.total_card = StatCard("Achats suivis")
        self.return_card = StatCard("Retours à prévoir")
        self.warranty_card = StatCard("Garanties à surveiller")
        self.month_total_card = StatCard("Dépenses du mois")
        self.activity = QListWidget()
        self.activity.setMinimumHeight(120)

        grid = QGridLayout()
        grid.addWidget(self.total_card, 0, 0)
        grid.addWidget(self.return_card, 0, 1)
        grid.addWidget(self.warranty_card, 0, 2)
        grid.addWidget(self.month_total_card, 0, 3)

        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addWidget(QLabel("Dernières activités"))
        layout.addWidget(self.activity)
        self.setLayout(layout)

    def update_stats(self, stats: Dict[str, object]) -> None:
        self.total_card.set_value(str(stats.get("total_items", 0)))
        self.return_card.set_value(str(stats.get("returns_due", 0)))
        self.warranty_card.set_value(str(stats.get("warranties_due", 0)))
        monthly = stats.get("monthly_total", 0.0)
        self.month_total_card.set_value(f"{float(monthly):.2f} €")
        self.activity.clear()
        for row in stats.get("recent_actions", []):
            item = QListWidgetItem(f"{row['ts']} · {row['action']}")
            self.activity.addItem(item)
