"""Database models and queries."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, List, Optional

import sqlite3


ItemRow = Dict[str, Any]


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row) -> ItemRow:
    return {key: row[key] for key in row.keys()}


def add_item(
    conn: sqlite3.Connection,
    data: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """Create an item and optional files."""
    ts = _now()
    payload = {
        "title": data["title"],
        "store": data["store"],
        "category": data["category"],
        "purchase_date": data["purchase_date"],
        "total_amount": data["total_amount"],
        "return_until": data["return_until"],
        "warranty_until": data["warranty_until"],
        "notes": data.get("notes", ""),
        "created_at": ts,
        "updated_at": ts,
    }
    cur = conn.execute(
        """
        INSERT INTO items
        (title, store, category, purchase_date, total_amount, return_until, warranty_until, notes, created_at, updated_at)
        VALUES (:title, :store, :category, :purchase_date, :total_amount, :return_until, :warranty_until, :notes, :created_at, :updated_at)
        """,
        payload,
    )
    item_id = int(cur.lastrowid)
    _sync_alerts(conn, item_id, data["return_until"], data["warranty_until"])
    if files:
        for file_data in files:
            add_file(conn, item_id, file_data)
    log_action(conn, "item_created", {"item_id": item_id, "title": data["title"]})
    return item_id


def update_item(conn: sqlite3.Connection, item_id: int, data: Dict[str, Any]) -> None:
    """Update an item."""
    data = {**data, "updated_at": _now(), "id": item_id}
    conn.execute(
        """
        UPDATE items
        SET title=:title,
            store=:store,
            category=:category,
            purchase_date=:purchase_date,
            total_amount=:total_amount,
            return_until=:return_until,
            warranty_until=:warranty_until,
            notes=:notes,
            updated_at=:updated_at
        WHERE id=:id
        """,
        data,
    )
    _sync_alerts(conn, item_id, data["return_until"], data["warranty_until"])
    log_action(conn, "item_updated", {"item_id": item_id})


def delete_item(conn: sqlite3.Connection, item_id: int) -> None:
    """Delete an item and related rows."""
    conn.execute("DELETE FROM items WHERE id=?", (item_id,))
    log_action(conn, "item_deleted", {"item_id": item_id})


def list_items(conn: sqlite3.Connection, filters: Optional[Dict[str, Any]] = None) -> List[ItemRow]:
    """List items applying filters."""
    filters = filters or {}
    clauses: List[str] = []
    params: Dict[str, Any] = {}

    if text := filters.get("text"):
        clauses.append("(title LIKE :text OR store LIKE :text OR category LIKE :text)")
        params["text"] = f"%{text}%"
    if store := filters.get("store"):
        clauses.append("store = :store")
        params["store"] = store
    if category := filters.get("category"):
        clauses.append("category = :category")
        params["category"] = category
    if start := filters.get("start"):
        clauses.append("purchase_date >= :start")
        params["start"] = start
    if end := filters.get("end"):
        clauses.append("purchase_date <= :end")
        params["end"] = end
    if due_return := filters.get("due_return"):
        clauses.append("return_until <= :due_return")
        params["due_return"] = due_return
    if due_warranty := filters.get("due_warranty"):
        clauses.append("warranty_until <= :due_warranty")
        params["due_warranty"] = due_warranty

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM items {where} ORDER BY purchase_date DESC"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_item(conn: sqlite3.Connection, item_id: int) -> Optional[ItemRow]:
    """Return a single item."""
    row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return _row_to_dict(row) if row else None


def add_file(conn: sqlite3.Connection, item_id: int, file_data: Dict[str, Any]) -> int:
    """Attach a file to an item."""
    cur = conn.execute(
        """
        INSERT INTO files (item_id, path, mime, size, checksum, uploaded_at)
        VALUES (:item_id, :path, :mime, :size, :checksum, :uploaded_at)
        """,
        {
            "item_id": item_id,
            "path": str(file_data["path"]),
            "mime": file_data["mime"],
            "size": file_data["size"],
            "checksum": file_data["checksum"],
            "uploaded_at": file_data["uploaded_at"],
        },
    )
    log_action(conn, "file_added", {"item_id": item_id, "path": str(file_data["path"])})
    return int(cur.lastrowid)


def list_files(conn: sqlite3.Connection, item_id: int) -> List[ItemRow]:
    """List files for an item."""
    rows = conn.execute("SELECT * FROM files WHERE item_id=? ORDER BY uploaded_at", (item_id,)).fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_file(conn: sqlite3.Connection, file_id: int) -> None:
    """Delete a file entry."""
    conn.execute("DELETE FROM files WHERE id=?", (file_id,))
    log_action(conn, "file_deleted", {"file_id": file_id})


def count_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Return dashboard metrics."""
    stats: Dict[str, Any] = {}
    stats["total_items"] = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    stats["returns_due"] = conn.execute(
        "SELECT COUNT(*) FROM items WHERE return_until <= date('now','+7 day')"
    ).fetchone()[0]
    stats["warranties_due"] = conn.execute(
        "SELECT COUNT(*) FROM items WHERE warranty_until <= date('now','+60 day')"
    ).fetchone()[0]
    stats["monthly_total"] = conn.execute(
        "SELECT IFNULL(SUM(total_amount),0) FROM items WHERE strftime('%Y-%m', purchase_date) = strftime('%Y-%m','now')"
    ).fetchone()[0]
    stats["recent_actions"] = [
        _row_to_dict(row)
        for row in conn.execute(
            "SELECT * FROM audit ORDER BY ts DESC LIMIT 5"
        )
    ]
    return stats


def log_action(conn: sqlite3.Connection, action: str, details: Dict[str, Any]) -> None:
    """Insert an audit log entry."""
    conn.execute(
        "INSERT INTO audit(action, details_json, ts) VALUES (?, ?, ?)",
        (action, json.dumps(details), _now()),
    )


def _sync_alerts(conn: sqlite3.Connection, item_id: int, return_until: str, warranty_until: str) -> None:
    """Ensure alert entries exist."""
    for alert_type, due in (("return", return_until), ("warranty", warranty_until)):
        row = conn.execute(
            "SELECT id FROM alerts WHERE item_id=? AND type=?",
            (item_id, alert_type),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE alerts SET due_on=?, sent_at=NULL WHERE id=?",
                (due, row[0]),
            )
        else:
            conn.execute(
                "INSERT INTO alerts(item_id, type, due_on) VALUES (?, ?, ?)",
                (item_id, alert_type, due),
            )


def list_due_alerts(conn: sqlite3.Connection) -> List[ItemRow]:
    """Return pending alerts."""
    rows = conn.execute(
        """
        SELECT alerts.id as alert_id, alerts.type, alerts.due_on, alerts.sent_at,
               items.id as item_id, items.title, items.store
        FROM alerts
        JOIN items ON items.id = alerts.item_id
        WHERE alerts.sent_at IS NULL AND alerts.due_on <= date('now')
        ORDER BY alerts.due_on
        """
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def mark_alert_sent(conn: sqlite3.Connection, alert_id: int) -> None:
    """Mark an alert as sent."""
    conn.execute(
        "UPDATE alerts SET sent_at=? WHERE id=?",
        (_now(), alert_id),
    )
