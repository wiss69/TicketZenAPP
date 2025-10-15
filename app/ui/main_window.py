"""Main application window."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QFutureWatcher, Qt, Slot
from PySide6.QtConcurrent import run as qt_run
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core import alerts, db, models, pdf_export, settings, storage, utils
from .widgets.add_item_dialog import AddItemDialog
from .widgets.dashboard import Dashboard
from .widgets.filters_bar import FiltersBar
from .widgets.item_table import ItemTable, ItemTableModel
from .widgets.preview_panel import PreviewPanel


class MainWindow(QMainWindow):
    """Main interface."""

    def __init__(self, user_settings: settings.UserSettings) -> None:
        super().__init__()
        self.settings = user_settings
        self.setWindowTitle("ProofPal Desktop")
        self.resize(1280, 720)
        self.model = ItemTableModel()
        self.table = ItemTable()
        self.table.setModel(self.model)
        self.filters = FiltersBar()
        self.dashboard = Dashboard()
        self.preview = PreviewPanel()
        self.files_list = QListWidget()
        self.files_list.setMinimumWidth(240)
        self.files_list.itemSelectionChanged.connect(self._on_file_selected)
        self.current_filters: Dict[str, str] = {}
        self._watchers: list[QFutureWatcher] = []

        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.dashboard)
        layout.addWidget(self.filters)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        splitter.addWidget(self.table)

        side = QWidget()
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.files_list)
        side_layout.addWidget(self.preview)
        side.setLayout(side_layout)
        splitter.addWidget(side)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Prêt")

        self._setup_toolbar()
        self._connect_signals()
        self.reload_items()
        self.refresh_dashboard()

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Actions")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.new_action = toolbar.addAction("Nouveau")
        self.import_action = toolbar.addAction("Importer fichier")
        self.export_action = toolbar.addAction("Exporter PDF")
        self.delete_action = toolbar.addAction("Supprimer")
        self.settings_action = toolbar.addAction("Paramètres")

        self.new_action.triggered.connect(self._create_item)
        self.import_action.triggered.connect(self._import_files)
        self.export_action.triggered.connect(self._export_pdf)
        self.delete_action.triggered.connect(self._delete_item)
        self.settings_action.triggered.connect(self._edit_settings)

    def _connect_signals(self) -> None:
        self.filters.filters_changed.connect(self._on_filters_changed)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    @Slot()
    def _on_filters_changed(self, filters: Dict[str, str]) -> None:
        self.current_filters = filters
        self.reload_items()

    def reload_items(self) -> None:
        with db.get_conn() as conn:
            items = models.list_items(conn, self.current_filters)
        self.model.set_items(items)
        self._populate_filter_options(items)
        self._clear_selection()

    def _populate_filter_options(self, items: list[Dict[str, object]]) -> None:
        stores = [str(item.get("store", "")) for item in items if item.get("store")]
        categories = [str(item.get("category", "")) for item in items if item.get("category")]
        self.filters.set_store_options(stores)
        self.filters.set_category_options(categories)

    def _clear_selection(self) -> None:
        self.table.clearSelection()
        self.files_list.clear()
        self.preview.clear()

    def refresh_dashboard(self) -> None:
        with db.get_conn() as conn:
            stats = models.count_stats(conn)
        self.dashboard.update_stats(stats)

    def _create_item(self) -> None:
        dialog = AddItemDialog(self.settings, self)
        if dialog.exec() != QDialog.Accepted:  # type: ignore[name-defined]
            return
        data = dialog.get_data()
        if not data:
            QMessageBox.warning(self, "Validation", "Le titre est requis")
            return
        files = dialog.get_files()
        with db.get_conn() as conn:
            item_id = models.add_item(conn, data)
            for file_path in files:
                stored = storage.copy_file_to_item(file_path, item_id)
                models.add_file(conn, item_id, stored)
        self.reload_items()
        self.refresh_dashboard()

    def _selected_item(self) -> Optional[Dict[str, object]]:
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        return self.model.item_at(index.row())

    def _on_selection_changed(self, *_args) -> None:
        item = self._selected_item()
        self.files_list.clear()
        self.preview.clear()
        if not item:
            return
        with db.get_conn() as conn:
            files = models.list_files(conn, int(item["id"]))
        for file_info in files:
            list_item = QListWidgetItem(Path(file_info["path"]).name)
            list_item.setData(Qt.UserRole, file_info)
            self.files_list.addItem(list_item)

    def _on_file_selected(self) -> None:
        selected = self.files_list.currentItem()
        if not selected:
            self.preview.clear()
            return
        info = selected.data(Qt.UserRole)
        if not info:
            return
        self.preview.show_file(Path(info["path"]))

    def _import_files(self) -> None:
        item = self._selected_item()
        if not item:
            QMessageBox.information(self, "Import", "Sélectionnez un achat pour importer des pièces.")
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Importer des fichiers")
        if not paths:
            return
        with db.get_conn() as conn:
            for path in paths:
                stored = storage.copy_file_to_item(Path(path), int(item["id"]))
                models.add_file(conn, int(item["id"]), stored)
        self._on_selection_changed()
        self.refresh_dashboard()

    def _delete_item(self) -> None:
        item = self._selected_item()
        if not item:
            return
        confirm = QMessageBox.question(
            self,
            "Supprimer",
            f"Supprimer {item['title']} ?",
        )
        if confirm != QMessageBox.Yes:
            return
        with db.get_conn() as conn:
            files = models.list_files(conn, int(item["id"]))
            models.delete_item(conn, int(item["id"]))
        for file_info in files:
            storage.remove_file(Path(file_info["path"]))
        self.reload_items()
        self.refresh_dashboard()

    def _export_pdf(self) -> None:
        item = self._selected_item()
        if not item:
            QMessageBox.information(self, "Export", "Sélectionnez un achat à exporter.")
            return
        dest = utils.documents_dir() / f"Dossier_SAV_{item['title']}_{item['purchase_date']}.pdf"
        progress = QProgressDialog("Génération en cours...", None, 0, 0, self)
        progress.setWindowTitle("Export PDF")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        future = qt_run(pdf_export.export_item_pdf, int(item["id"]), dest)
        watcher: QFutureWatcher = QFutureWatcher()
        watcher.setFuture(future)

        def finished() -> None:
            progress.close()
            if watcher.future().result():
                QMessageBox.information(self, "Export", f"PDF généré dans {dest}")
            self._watchers.remove(watcher)

        watcher.finished.connect(finished)
        self._watchers.append(watcher)

    def _edit_settings(self) -> None:
        QMessageBox.information(
            self,
            "Paramètres",
            "Les paramètres détaillés seront disponibles dans une prochaine version."
        )

    def notify_due_alerts(self) -> None:
        with db.get_conn() as conn:
            count = alerts.check_due(conn)
        if count:
            self.statusBar().showMessage(f"{count} rappel(s) envoyé(s)", 5000)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.settings.last_opened = datetime.now().isoformat(timespec="seconds")
        settings.save_settings(self.settings)
        super().closeEvent(event)

    def statusBar(self) -> QStatusBar:  # type: ignore[override]
        return super().statusBar()
