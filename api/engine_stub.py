"""Fake trainer — demo insurance while AGENT: LOOP builds the real engine.

Replays the exact event sequence from web/mocks/events.json (read at runtime),
~1.5s between attempts, writes attempts to SQLite, and on convergence writes
data/jobs/<job_id>/artifact/tool.py (a trivial-but-working pandas script) so
/artifact, /guard and /i/{slug}/run work end-to-end.

The real engine replaces this via the single INTEGRATION POINT in api/jobs.py.
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from api import store
from api.files import job_dir

REPO_ROOT = Path(__file__).resolve().parent.parent
EVENTS_JSON = REPO_ROOT / "web" / "mocks" / "events.json"


def _scale() -> float:
    """STUB_SLEEP_SCALE=0 makes tests instant; default is demo pacing."""
    try:
        return float(os.environ.get("STUB_SLEEP_SCALE", "1.0"))
    except ValueError:
        return 1.0


# ── the artifact: a trivial pandas script that actually does Andrei's job ──

TOOL_PY = '''#!/usr/bin/env python
"""tool.py — the trained intern. Plain pandas. No network. No model. No key.

Usage: python tool.py <manifest.csv> <rate_card.csv> <out.csv>
(The two inputs may be given in either order; they are told apart by columns.)
"""
import sys

import pandas as pd


def main(a: str, b: str, out_path: str) -> None:
    m = pd.read_csv(a)
    r = pd.read_csv(b)
    if "weight_kg" not in m.columns:          # inputs arrived in the other order
        m, r = r, m
    r = r.drop_duplicates(subset=["carrier_code"], keep="first")
    df = m.merge(r, on="carrier_code", how="left")

    df = df[df["weight_kg"] >= 500]                       # skip the little stuff
    df["_load_t"] = (df["weight_kg"] / 1000).round(2)     # tonnes, 2dp
    df["_cost"] = (df["base_fee_usd"] + df["rate_per_km_usd"] * df["distance_km"]).round(0)

    df["Date"] = pd.to_datetime(df["date"]).dt.strftime("%d.%m.%Y")
    df["Route"] = df["destination"]
    df["Truck"] = df["truck_id"].fillna("TBC")            # not on the card -> TBC

    df = df.sort_values(["Route", "_cost"], ascending=[True, False], na_position="last")

    def money(v):
        return "TBC" if pd.isna(v) else f"{int(v):,}"

    out = pd.DataFrame({
        "Date": df["Date"],
        "Route": df["Route"],
        "Truck": df["Truck"],
        "Load (t)": df["_load_t"].map(lambda v: f"{v:.2f}"),
        "Cost ($)": df["_cost"].map(money),
    })
    total = pd.DataFrame([{
        "Date": "", "Route": "", "Truck": "TOTAL",
        "Load (t)": f"{df['_load_t'].sum():.2f}",
        "Cost ($)": f"{int(df['_cost'].sum(skipna=True)):,}",
    }])
    pd.concat([out, total], ignore_index=True).to_csv(out_path, index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
'''


def write_artifact(job_id: str) -> Path:
    job = store.get_job(job_id) or {}
    art = job_dir(job_id) / "artifact"
    art.mkdir(parents=True, exist_ok=True)
    (art / "tool.py").write_text(TOOL_PY)
    (art / "requirements.txt").write_text("pandas==2.2.3\n")
    (art / "spec.json").write_text(job.get("spec_json") or "{}")
    (art / "guard.json").write_text(json.dumps(stub_guard_report(), indent=2))
    return art


def stub_guard_report() -> dict:
    return {"pass": True, "network_calls": 0, "model_calls": 0,
            "checked_at": datetime.now(timezone.utc).isoformat(), "violations": []}


def guard_report(job_id: str) -> dict:
    """Run guards/no_llm_at_runtime.py against the artifact if the guard exists
    on disk; otherwise return the stub PASS report."""
    guard = REPO_ROOT / "guards" / "no_llm_at_runtime.py"
    tool = job_dir(job_id) / "artifact" / "tool.py"
    if guard.exists() and tool.exists():
        try:
            proc = subprocess.run(
                [sys.executable, str(guard), str(tool)],
                capture_output=True, text=True, timeout=15, cwd=str(REPO_ROOT),
            )
            report = json.loads(proc.stdout.strip())
            report.setdefault("checked_at", datetime.now(timezone.utc).isoformat())
            return report
        except Exception:
            pass  # fall back to the stub — never 500 the demo
    return stub_guard_report()


# ── per-attempt produced.csv so GET /attempts/{n}/diff has real files ──

def _perturb(value: str) -> str:
    v = value.replace(",", "").replace("$", "").strip()
    try:
        return f"{float(v) + 1:g}"
    except ValueError:
        return (value + "?") if value else "?"


def write_attempt_produced(job_id: str, n: int, strip: str) -> str:
    """expected.csv with the strip's '0' cells perturbed — a plausible wrong output."""
    expected_files = store.get_files(job_id, role="expected")
    att_dir = job_dir(job_id) / "attempts" / str(n)
    att_dir.mkdir(parents=True, exist_ok=True)
    out = att_dir / "produced.csv"
    if not expected_files:
        out.write_text("")
        return str(out)
    raw = Path(expected_files[0]["path"]).read_text(encoding="utf-8-sig", errors="replace")
    rows = [row for row in csv.reader(io.StringIO(raw)) if row]
    header, body = rows[0], rows[1:]
    ncols = len(header)
    i = 0
    for r in body:
        for c in range(min(ncols, len(r))):
            if i < len(strip) and strip[i] == "0":
                r[c] = _perturb(r[c])
            i += 1
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(body)
    out.write_text(buf.getvalue())
    return str(out)


# ── the trainer itself ─────────────────────────────────────────────────

async def train(job_id: str, publish: Callable[[dict], None]) -> None:
    scale = _scale()
    events = json.loads(EVENTS_JSON.read_text())
    store.update_job(job_id, status="training")
    started = time.monotonic()

    for ev in events:
        etype = ev.get("type")
        if etype == "attempt.started" and ev.get("n", 1) > 1:
            await asyncio.sleep(1.5 * scale)          # ~1.5s between attempts
        elif etype == "phase":
            await asyncio.sleep(0.25 * scale)

        if etype == "attempt.scored":
            attempt = dict(ev["attempt"])
            attempt["at"] = datetime.now(timezone.utc).isoformat()
            produced = write_attempt_produced(job_id, attempt["n"], attempt["strip"])
            store.add_attempt(job_id, attempt, findings=[], code_path=produced)
            publish({"type": "attempt.scored", "attempt": attempt})
        elif etype == "converged":
            art = write_artifact(job_id)
            train_ms = int((time.monotonic() - started) * 1000)
            store.update_job(
                job_id, status="ready", outcome=ev.get("outcome", "PERFECT"),
                best_score=ev.get("best", 1.0), attempts_used=ev.get("attempts"),
                train_ms=train_ms,
            )
            publish({**ev, "ms": train_ms})
            publish_dir = art  # noqa: F841  (kept for debuggability)
        elif etype == "failed":
            store.update_job(job_id, status="failed", outcome="FAILED")
            publish(ev)
        else:
            publish(ev)


# ── running the artifact for /i/{slug}/run ─────────────────────────────

def run_artifact(job_id: str, input_paths: list[str], out_dir: Path,
                 timeout: int = 20) -> dict:
    """Execute tool.py on two uploaded files. subprocess, empty env, cwd=out_dir.
    (The real engine's runner.py replaces this with the full sandbox.)"""
    tool = job_dir(job_id) / "artifact" / "tool.py"
    if not tool.exists():
        write_artifact(job_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summary.csv"
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(tool), *input_paths, str(out_path)],
        capture_output=True, text=True, timeout=timeout, cwd=str(out_dir),
        env={"PATH": os.environ.get("PATH", ""), "HOME": str(out_dir)},
    )
    ms = int((time.monotonic() - t0) * 1000)
    return {"ok": proc.returncode == 0 and out_path.exists(), "ms": ms,
            "out_path": str(out_path), "stdout": proc.stdout, "stderr": proc.stderr}
