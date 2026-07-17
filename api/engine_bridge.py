"""Bridge: the API's async train(job_id, publish) contract → the real engine loop.

The engine's orchestrator is synchronous (it shells out to the sandbox and the
scorer); we run it in a worker thread and marshal every LoopEvent back onto the
event loop for the SSE bus. Attempt rows land in SQLite as they are scored, so a
refresh mid-training rebuilds the Ledger.
"""
from __future__ import annotations

import asyncio
import json
from typing import Callable

from api import store
from engine import llm as engine_llm
from engine import orchestrator


async def train(job_id: str, publish: Callable[[dict], None]) -> None:
    job = store.get_job(job_id)
    if not job or not job.get("spec_json"):
        publish({"type": "failed", "reason": "No approved spec for this job.",
                 "hint": "Go back to the read-back and approve the job first."})
        return

    spec = json.loads(job["spec_json"])
    inputs = store.get_files(job_id, role="input")
    expected = store.get_files(job_id, role="expected")
    if len(inputs) < 2 or not expected:
        publish({"type": "failed",
                 "reason": "I need the two files you start with and the one you finished.",
                 "hint": "Upload 2 input files and 1 expected output."})
        return

    store.update_job(job_id, status="training")
    job_dir = store.data_dir() / "jobs" / job_id
    loop = asyncio.get_running_loop()

    def emit(ev: dict) -> None:
        if ev.get("type") == "attempt.scored":
            n = ev["attempt"]["n"]
            # the diff endpoint reads the produced CSV from code_path
            store.add_attempt(job_id, ev["attempt"], findings=[],
                              code_path=str(job_dir / "attempts" / f"attempt_{n}_out.csv"))
        loop.call_soon_threadsafe(publish, ev)

    try:
        result = await asyncio.to_thread(
            orchestrator.train,
            job_dir, spec,
            # canonical input order: sorted by filename. Uploads race in the
            # browser, and argv order is baked into both the prompt (cassette
            # key) and the trained script — every caller must sort the same way
            sorted([f["path"] for f in inputs[:2]],
                   key=lambda p: p.rsplit("/", 1)[-1].casefold()),
            expected[0]["path"],
            engine_llm.get_llm(),
            emit,
        )
    except Exception as exc:  # engine crash must terminate the SSE stream
        store.update_job(job_id, status="failed", outcome="FAILED")
        publish({"type": "failed",
                 "reason": "Training hit an internal error.",
                 "hint": str(exc)[:200]})
        return

    if result.get("outcome") == "FAILED":
        store.update_job(job_id, status="failed", outcome="FAILED",
                         best_score=result.get("best"),
                         attempts_used=result.get("attempts"),
                         train_ms=result.get("ms"))
    else:
        store.update_job(job_id, status="ready",
                         outcome=result.get("outcome"),
                         best_score=result.get("best"),
                         attempts_used=result.get("attempts"),
                         train_ms=result.get("ms"))
