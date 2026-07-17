"""engine/events.py — LoopEvent emitter.

Events are plain dicts shaped exactly like api/schemas.py's LoopEvent union
(that file is the contract; tests validate against it). One JSON per line on
stdout so the CLI and the API's SSE bus consume the same stream.
"""
from __future__ import annotations

import json
import sys
from typing import Callable

Emitter = Callable[[dict], None]


def stdout_emitter(event: dict) -> None:
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def phase(phase_name: str) -> dict:
    return {"type": "phase", "phase": phase_name}


def attempt_started(n: int) -> dict:
    return {"type": "attempt.started", "n": n}


def attempt_scored(n: int, score: float, cells_ok: int, cells_total: int,
                   strip: str, headline: str, changed: str,
                   duration_ms: int, at: str) -> dict:
    return {"type": "attempt.scored",
            "attempt": {"n": n, "score": score, "cells_ok": cells_ok,
                        "cells_total": cells_total, "strip": strip,
                        "headline": headline, "changed": changed,
                        "duration_ms": duration_ms, "at": at}}


def converged(outcome: str, best: float, attempts: int, ms: int) -> dict:
    return {"type": "converged", "outcome": outcome, "best": best,
            "attempts": attempts, "ms": ms}


def failed(reason: str, hint: str) -> dict:
    return {"type": "failed", "reason": reason, "hint": hint}


def log(line: str) -> dict:
    return {"type": "log", "line": line}
