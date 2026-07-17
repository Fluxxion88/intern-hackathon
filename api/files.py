"""Upload handling: save to data/jobs/<job_id>/<role-dir>/, sniff CSV, build preview."""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from api import store

PREVIEW_ROWS = 20

ROLE_DIR = {"input": "inputs", "expected": "expected", "today": "inputs"}


def job_dir(job_id: str) -> Path:
    return store.data_dir() / "jobs" / job_id


def safe_filename(name: str) -> str:
    name = Path(name or "upload.csv").name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "upload.csv"


def sniff_dialect(text: str) -> csv.Dialect:
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")  # type: ignore[return-value]
    except csv.Error:
        return csv.excel  # default comma


def preview_csv(raw: bytes) -> dict:
    """→ {columns, rows, truncated} per FilePreview."""
    text = raw.decode("utf-8-sig", errors="replace")
    dialect = sniff_dialect(text)
    reader = csv.reader(io.StringIO(text), dialect)
    rows = []
    columns: list[str] = []
    truncated = False
    for i, row in enumerate(reader):
        if not row:
            continue
        if i == 0:
            columns = [c.strip() for c in row]
            continue
        if len(rows) >= PREVIEW_ROWS:
            truncated = True
            break
        rows.append([c.strip() for c in row])
    return {"columns": columns, "rows": rows, "truncated": truncated}


def save_upload(job_id: str, role: str, filename: str, raw: bytes) -> tuple[dict, dict]:
    """Persist bytes + DB row. Returns (file_record, preview)."""
    fname = safe_filename(filename)
    dest_dir = job_dir(job_id) / ROLE_DIR.get(role, "inputs")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname
    dest.write_bytes(raw)
    preview = preview_csv(raw)
    rec = store.add_file(job_id, role, fname, str(dest), len(raw), preview)
    return rec, preview
