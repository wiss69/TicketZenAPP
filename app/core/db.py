"""Database helpers."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from . import utils


def init_db(path: Path | None = None) -> None:
    """Initialise the SQLite database."""
    db_path = path or utils.database_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            store TEXT NOT NULL,
            category TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            return_until TEXT NOT NULL,
            warranty_until TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            path TEXT NOT NULL,
            mime TEXT NOT NULL,
            size INTEGER NOT NULL,
            checksum TEXT NOT NULL,
            uploaded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK(type IN ('return','warranty')),
            due_on TEXT NOT NULL,
            sent_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details_json TEXT NOT NULL,
            ts TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


@contextmanager
def get_conn(path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield a connection with sensible defaults."""
    db_path = path or utils.database_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
