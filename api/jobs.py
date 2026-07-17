"""In-process job execution: asyncio task registry + per-job event bus WITH REPLAY.

docs/04 §6+§8: no Celery, no Redis. The bus keeps EVERY event for a job in memory;
a new SSE subscriber gets the full backlog first, then live events. Andrei will
refresh mid-training and the Ledger must come back full.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Awaitable, Callable, Optional

from api import store

TERMINAL_TYPES = {"converged", "failed"}


class EventBus:
    def __init__(self) -> None:
        self._history: dict[str, list[dict]] = {}
        self._subscribers: dict[str, set[asyncio.Queue]] = {}

    def publish(self, job_id: str, event: dict) -> None:
        self._history.setdefault(job_id, []).append(event)
        for q in self._subscribers.get(job_id, set()).copy():
            q.put_nowait(event)

    def history(self, job_id: str) -> list[dict]:
        return list(self._history.get(job_id, []))

    def finished(self, job_id: str) -> bool:
        return any(ev.get("type") in TERMINAL_TYPES for ev in self._history.get(job_id, []))

    async def subscribe(self, job_id: str) -> AsyncIterator[dict]:
        """Backlog first, then live. Ends after a terminal event."""
        backlog = self.history(job_id)
        for ev in backlog:
            yield ev
            if ev.get("type") in TERMINAL_TYPES:
                return
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(job_id, set()).add(q)
        try:
            while True:
                ev = await q.get()
                yield ev
                if ev.get("type") in TERMINAL_TYPES:
                    return
        finally:
            self._subscribers.get(job_id, set()).discard(q)


bus = EventBus()

_tasks: dict[str, asyncio.Task] = {}

Trainer = Callable[[str, Callable[[dict], None]], Awaitable[None]]


def get_trainer() -> Trainer:
    # INTEGRATION POINT ──────────────────────────────────────────────────
    # This is the ONE place the real engine gets wired in. To swap the stub
    # for the real loop, replace the two lines below with:
    #
    #     from engine.orchestrator import train
    #     return train
    #
    # Contract: `async def train(job_id: str, publish: Callable[[dict], None])`
    #   - reads spec/files from api.store (spec_json on the job row, files table)
    #   - calls publish(event_dict) for every LoopEvent (schemas.LoopEvent shapes)
    #   - writes attempt rows via store.add_attempt as they are scored
    #   - on convergence: writes data/jobs/<job_id>/artifact/{tool.py,
    #     requirements.txt, spec.json, guard.json} and updates the job row
    #     (status/outcome/best_score/attempts_used/train_ms)
    #   - MUST emit a terminal event ({"type":"converged",...} or {"type":"failed",...})
    # ────────────────────────────────────────────────────────────────────
    from api import engine_stub
    return engine_stub.train


def is_training(job_id: str) -> bool:
    t = _tasks.get(job_id)
    return t is not None and not t.done()


def start_training(job_id: str) -> None:
    """Idempotent: a second POST /train just keeps the existing stream."""
    if is_training(job_id) or bus.finished(job_id):
        return
    trainer = get_trainer()

    def _publish(ev: dict) -> None:
        bus.publish(job_id, ev)

    async def _run() -> None:
        try:
            await trainer(job_id, _publish)
        except Exception as exc:  # never let the stream hang open forever
            store.update_job(job_id, status="failed", outcome="FAILED")
            bus.publish(job_id, {"type": "failed", "reason": str(exc),
                                 "hint": "Something broke on our side. Try training again."})

    _tasks[job_id] = asyncio.get_event_loop().create_task(_run())


def replay_or_rebuild(job_id: str) -> Optional[list[dict]]:
    """If the process restarted mid-way, rebuild a terminal backlog from SQLite
    so a late SSE subscriber still sees the attempts instead of an empty ledger."""
    if bus.history(job_id):
        return None
    job = store.get_job(job_id)
    if not job or job["status"] not in ("ready", "failed"):
        return None
    events: list[dict] = []
    for a in store.get_attempts(job_id):
        events.append({"type": "attempt.started", "n": a["n"]})
        events.append({"type": "attempt.scored", "attempt": {
            "n": a["n"], "score": a["score"], "cells_ok": a["cells_ok"],
            "cells_total": a["cells_total"], "strip": a["strip"],
            "headline": a["headline"], "changed": a["changed"],
            "duration_ms": a["duration_ms"], "at": a["created_at"]}})
    if job["status"] == "ready":
        events.append({"type": "converged", "outcome": job["outcome"] or "PERFECT",
                       "best": job["best_score"] or 0.0,
                       "attempts": job["attempts_used"] or len(store.get_attempts(job_id)),
                       "ms": job["train_ms"] or 0})
    else:
        events.append({"type": "failed", "reason": "training failed",
                       "hint": "Check the spec and try again."})
    for ev in events:
        bus.publish(job_id, ev)
    return events


def event_json(ev: Any) -> str:
    return json.dumps(ev, separators=(",", ":"))
