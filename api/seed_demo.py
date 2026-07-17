"""Seed a demo-ready state on a fresh deployment: Andrei's trained intern.

Run once at container start (SEED_DEMO=1). With LLM_PROVIDER=mock this replays
the recorded training run (~1s, zero network) and leaves the DB + artifact in
the exact state the live walkthrough produces: /i/andrei-dispatch works
immediately, and GET /api/jobs/<id> rebuilds the full Ledger.

Idempotent: skips if the slug already exists.

  .venv/bin/python -m api.seed_demo
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from api import files as files_mod
from api import store
from api.main import CANNED_GUESSES, CANNED_RULES, OUTPUT_COLUMNS
from engine import orchestrator
from engine.llm import get_llm

REPO_ROOT = Path(__file__).resolve().parent.parent
MOCK = REPO_ROOT / "mock"
SLUG = "andrei-dispatch"
BRIEF = json.loads((MOCK / "brief.json").read_text())["brief"]


def main() -> int:
    store.init_db()
    if store.get_job_by_slug(SLUG):
        print(f"seed: {SLUG} already present, nothing to do")
        return 0

    user = store.create_user("Andrei", "andrei@example.com")
    job = store.create_job(user["id"], BRIEF, SLUG, questions=[])
    spec = {"rules": CANNED_RULES, "guesses": CANNED_GUESSES,
            "output_columns": OUTPUT_COLUMNS, "slug": SLUG}
    store.update_job(job["id"], spec_json=json.dumps(spec), status="training")

    job_dir = store.data_dir() / "jobs" / job["id"]
    inputs_dir = job_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    uploads = [("input", "carrier_rates_2026-07.csv"),
               ("input", "manifest_2026-07-14.csv"),
               ("expected", "dispatch_summary_14.07.csv")]
    paths: dict[str, list[str]] = {"input": [], "expected": []}
    for role, name in uploads:
        dest = inputs_dir / name
        shutil.copyfile(MOCK / name, dest)
        preview = files_mod.preview_csv(dest.read_bytes())
        store.add_file(job["id"], role, name, str(dest), dest.stat().st_size, preview)
        paths[role].append(str(dest))

    def emit(ev: dict) -> None:
        if ev.get("type") == "attempt.scored":
            n = ev["attempt"]["n"]
            store.add_attempt(job["id"], ev["attempt"], findings=[],
                              code_path=str(job_dir / "attempts" / f"attempt_{n}_out.csv"))
        if ev.get("type") in ("attempt.scored", "converged", "failed"):
            print("seed:", json.dumps(ev)[:120])

    result = orchestrator.train(
        job_dir, spec,
        sorted(paths["input"], key=lambda p: p.rsplit("/", 1)[-1].casefold()),
        paths["expected"][0], get_llm(), emit)

    if result.get("outcome") != "PERFECT":
        store.update_job(job["id"], status="failed", outcome=result.get("outcome"))
        print(f"seed: training did not converge ({result.get('outcome')})", file=sys.stderr)
        return 1
    store.update_job(job["id"], status="ready", outcome="PERFECT",
                     best_score=result.get("best"),
                     attempts_used=result.get("attempts"),
                     train_ms=result.get("ms"))
    print(f"seed: {SLUG} ready — {result['attempts']} attempts, best {result['best']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
