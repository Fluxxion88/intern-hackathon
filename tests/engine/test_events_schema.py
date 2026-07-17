"""Every event the engine emits must validate against api/schemas.py LoopEvent."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from pydantic import TypeAdapter

from engine import events

REPO = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod   # pydantic resolves forward refs via sys.modules
    spec.loader.exec_module(mod)
    return mod


schemas = _load("api_schemas", REPO / "api" / "schemas.py")
ADAPTER = TypeAdapter(schemas.LoopEvent)


def test_all_event_shapes_validate():
    samples = [
        events.phase("WRITING"),
        events.phase("RUNNING"),
        events.phase("CHECKING"),
        events.phase("FIXING"),
        events.attempt_started(1),
        events.attempt_scored(1, 0.41, 20, 50, "10" * 25,
                              "Read both files. Guessed at your column names.",
                              "wrote the first version", 5300,
                              "2026-07-17T20:00:00+00:00"),
        events.converged("PERFECT", 1.0, 5, 42000),
        events.failed("anti_cheat", "hardcoded target values"),
        events.log("dev only"),
    ]
    for ev in samples:
        ADAPTER.validate_python(ev)   # raises on contract drift
