"""PDF export helper."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from . import db, models, utils


def _create_canvas(dest: Path) -> canvas.Canvas:
    dest.parent.mkdir(parents=True, exist_ok=True)
    return canvas.Canvas(str(dest), pagesize=A4)


def _draw_header(c: canvas.Canvas, title: str) -> None:
    c.setFont("Helvetica-Bold", 22)
    c.drawString(2.5 * cm, 27 * cm, "Dossier SAV")
    c.setFont("Helvetica", 14)
    c.drawString(2.5 * cm, 25.8 * cm, title)
    c.setLineWidth(1)
    c.line(2.5 * cm, 25.5 * cm, 18 * cm, 25.5 * cm)


def _draw_metadata(c: canvas.Canvas, item: models.ItemRow) -> None:
    y = 24 * cm
    c.setFont("Helvetica", 11)
    fields = [
        ("Magasin", item["store"]),
        ("Catégorie", item["category"]),
        ("Achat", item["purchase_date"]),
        ("Montant", utils.format_money(item["total_amount"])),
        ("Retour jusqu'au", item["return_until"]),
        ("Garantie jusqu'au", item["warranty_until"]),
    ]
    for label, value in fields:
        c.drawString(2.5 * cm, y, f"{label} : {value}")
        y -= 0.8 * cm
    if item.get("notes"):
        c.drawString(2.5 * cm, y, "Notes :")
        text = c.beginText(3 * cm, y - 0.6 * cm)
        text.setFont("Helvetica", 10)
        text.textLines(item["notes"])
        c.drawText(text)


def _prepare_preview(path: Path, workspace: Path) -> Path:
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(path)
        if doc.page_count == 0:
            return path
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        temp = workspace / f"{path.stem}_preview.png"
        pix.save(temp)
        return temp
    return path


def _draw_attachments(c: canvas.Canvas, files: List[models.ItemRow], workspace: Path) -> None:
    if not files:
        return
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2.5 * cm, 27 * cm, "Pièces jointes")
    x = 2.5 * cm
    y = 25 * cm
    max_width = 8 * cm
    max_height = 8 * cm
    for file_info in files:
        preview_path = _prepare_preview(Path(file_info["path"]), workspace)
        try:
            image = ImageReader(str(preview_path))
        except Exception:
            c.setFont("Helvetica", 10)
            c.drawString(x, y, f"Aperçu indisponible pour {Path(file_info['path']).name}")
            y -= 1 * cm
            continue
        iw, ih = image.getSize()
        ratio = min(max_width / iw, max_height / ih)
        width = iw * ratio
        height = ih * ratio
        c.drawImage(image, x, y - height, width=width, height=height, preserveAspectRatio=True)
        c.setFont("Helvetica", 9)
        c.drawString(x, y - height - 0.3 * cm, Path(file_info["path"]).name)
        x += max_width + 1 * cm
        if x + max_width > 18 * cm:
            x = 2.5 * cm
            y -= max_height + 2 * cm
            if y < 5 * cm:
                c.showPage()
                y = 25 * cm


def export_item_pdf(item_id: int, dest: Path) -> Path:
    """Export an item as PDF dossier."""
    with db.get_conn() as conn:
        item = models.get_item(conn, item_id)
        if not item:
            raise ValueError(f"Item {item_id} introuvable")
        files = models.list_files(conn, item_id)
    c = _create_canvas(dest)
    _draw_header(c, item["title"])
    _draw_metadata(c, item)
    with TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        _draw_attachments(c, files, workspace)
    c.showPage()
    c.setFont("Helvetica", 8)
    c.drawString(2 * cm, 2 * cm, f"Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.save()
    return dest
