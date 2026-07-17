"""Zero.xyz adapter — the intern's hands.

When the runner reports a CRASH finding whose hint matches a capability gap
(scanned PDF, xlsx-with-macros, an unreachable format), we do NOT hand the
model a bigger prompt. We hand it a capability.

Boundary (docs/07 §2.1, and it is a feature, not a workaround): Zero is used at
TRAINING time, by the trainer. The learned extraction step is baked into the
deterministic artifact. The shipped tool still has no network — the guard
(guards/no_llm_at_runtime.py) stays green. Zero remains live at runtime only on
the email transport path, which is outside the transform and outside the guard's
scope by design.

ZERO_MODE=mock (default) replays a recorded discovery+call so the demo never
depends on the network. TODO(sponsor): flip to live after `zero auth login`
and record the discovery the moment it works.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

MOCK_DIR = Path(__file__).resolve().parent / "recordings"


@dataclass
class Capability:
    need: str          # "extract a table from a scanned PDF"
    service: str       # discovered service name
    call: str          # how the trainer invoked it (recorded)
    result_path: str   # the extracted artifact baked into training


class ZeroAdapter:
    def __init__(self, mode: str | None = None):
        self.mode = mode or os.environ.get("ZERO_MODE", "mock")

    def resolve(self, need: str) -> Capability | None:
        """Discover a service for a capability gap. Mock replays a recording."""
        if self.mode == "mock":
            rec = MOCK_DIR / "zero_pdf_extract.json"
            if rec.exists():
                d = json.loads(rec.read_text())
                return Capability(**d)
            return None
        # TODO(sponsor): live path — Zero programmatic discovery from engine/,
        # not the CLI. Ask in the Zero Discord for the non-CLI entrypoint.
        raise NotImplementedError("ZERO_MODE=live not wired; use mock")
