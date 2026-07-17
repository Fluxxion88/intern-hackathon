"""SQLite store — the exact 5 tables from docs/04-ARCHITECTURE.md §3.

Path is env-overridable (INTERN_DATA_DIR) so tests can use a throwaway dir.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  slug TEXT UNIQUE,
  brief TEXT NOT NULL,
  questions_json TEXT,
  spec_json TEXT,
  status TEXT NOT NULL,
  outcome TEXT,
  best_score REAL,
  attempts_used INTEGER,
  train_ms INTEGER,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  role TEXT NOT NULL,
  filename TEXT NOT NULL,
  path TEXT NOT NULL,
  bytes INTEGER,
  preview_json TEXT
);
CREATE TABLE IF NOT EXISTS attempts (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  n INTEGER NOT NULL,
  score REAL,
  cells_ok INTEGER, cells_total INTEGER,
  strip TEXT,
  findings_json TEXT,
  headline TEXT,
  changed TEXT,
  code_path TEXT,
  stdout TEXT, stderr TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  duration_ms INTEGER,
  ok INTEGER,
  created_at TEXT NOT NULL
);
"""


def data_dir() -> Path:
    return Path(os.environ.get("INTERN_DATA_DIR", str(REPO_ROOT / "data")))


def db_path() -> Path:
    return data_dir() / "intern.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid.uuid4().hex


def connect() -> sqlite3.Connection:
    data_dir().mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def _row(r: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return dict(r) if r is not None else None


# ── users ──────────────────────────────────────────────────────────────

def create_user(name: str, email: str) -> dict:
    user = {"id": new_id(), "name": name, "email": email, "created_at": now_iso()}
    with connect() as conn:
        conn.execute(
            "INSERT INTO users (id, name, email, created_at) VALUES (?,?,?,?)",
            (user["id"], user["name"], user["email"], user["created_at"]),
        )
    return user


def get_user(user_id: str) -> Optional[dict]:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())


# ── jobs ───────────────────────────────────────────────────────────────

def create_job(user_id: str, brief: str, slug: str, questions: list[dict]) -> dict:
    job_id = new_id()
    with connect() as conn:
        conn.execute(
            "INSERT INTO jobs (id, user_id, slug, brief, questions_json, status, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (job_id, user_id, slug, brief, json.dumps(questions), "questioning", now_iso()),
        )
    return get_job(job_id)  # type: ignore[return-value]


def get_job(job_id: str) -> Optional[dict]:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())


def get_job_by_slug(slug: str) -> Optional[dict]:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM jobs WHERE slug=?", (slug,)).fetchone())


def slug_exists(slug: str) -> bool:
    with connect() as conn:
        return conn.execute("SELECT 1 FROM jobs WHERE slug=?", (slug,)).fetchone() is not None


def update_job(job_id: str, **fields: Any) -> Optional[dict]:
    if fields:
        cols = ", ".join(f"{k}=?" for k in fields)
        with connect() as conn:
            conn.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), job_id))
    return get_job(job_id)


# ── files ──────────────────────────────────────────────────────────────

def add_file(job_id: str, role: str, filename: str, path: str, nbytes: int,
             preview: dict) -> dict:
    file_id = new_id()
    with connect() as conn:
        conn.execute(
            "INSERT INTO files (id, job_id, role, filename, path, bytes, preview_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (file_id, job_id, role, filename, path, nbytes, json.dumps(preview)),
        )
    return {"id": file_id, "job_id": job_id, "role": role, "filename": filename,
            "path": path, "bytes": nbytes, "preview_json": json.dumps(preview)}


def get_files(job_id: str, role: Optional[str] = None) -> list[dict]:
    q = "SELECT * FROM files WHERE job_id=?"
    args: tuple = (job_id,)
    if role:
        q += " AND role=?"
        args = (job_id, role)
    with connect() as conn:
        return [dict(r) for r in conn.execute(q, args).fetchall()]


# ── attempts ───────────────────────────────────────────────────────────

def add_attempt(job_id: str, attempt: dict, findings: Optional[list] = None,
                code_path: str = "", stdout: str = "", stderr: str = "") -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO attempts (id, job_id, n, score, cells_ok, cells_total, strip,"
            " findings_json, headline, changed, code_path, stdout, stderr, duration_ms, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (new_id(), job_id, attempt["n"], attempt["score"], attempt["cells_ok"],
             attempt["cells_total"], attempt["strip"], json.dumps(findings or []),
             attempt["headline"], attempt["changed"], code_path, stdout, stderr,
             attempt["duration_ms"], attempt.get("at") or now_iso()),
        )


def get_attempts(job_id: str) -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM attempts WHERE job_id=? ORDER BY n", (job_id,)).fetchall()]


def get_attempt(job_id: str, n: int) -> Optional[dict]:
    with connect() as conn:
        return _row(conn.execute(
            "SELECT * FROM attempts WHERE job_id=? AND n=?", (job_id, n)).fetchone())


# ── runs ───────────────────────────────────────────────────────────────

def add_run(job_id: str, duration_ms: int, ok: bool) -> dict:
    run = {"id": new_id(), "job_id": job_id, "duration_ms": duration_ms,
           "ok": 1 if ok else 0, "created_at": now_iso()}
    with connect() as conn:
        conn.execute(
            "INSERT INTO runs (id, job_id, duration_ms, ok, created_at) VALUES (?,?,?,?,?)",
            (run["id"], run["job_id"], run["duration_ms"], run["ok"], run["created_at"]),
        )
    return run
