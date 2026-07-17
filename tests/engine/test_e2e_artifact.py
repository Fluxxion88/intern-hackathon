"""E2E: the trained artifact, run on files it has NEVER seen (the 17th),
must byte-equal the reference. Passing this is the empirical anti-cheat:
the loop learned the rules, not the answers.

Skips (with a loud reason) until an artifact has been trained via
`python -m engine.cli train --fixture mock/`.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from engine.runner import run as sandbox_run

REPO = Path(__file__).resolve().parents[2]
MOCK = REPO / "mock"
ARTIFACT = REPO / "data" / "jobs" / "andrei-dispatch" / "artifact"

pytestmark = pytest.mark.skipif(
    not (ARTIFACT / "tool.py").exists(),
    reason="no trained artifact yet — run: python -m engine.cli train --fixture mock/",
)


def test_artifact_generalises_to_unseen_day():
    rr = sandbox_run(ARTIFACT / "tool.py",
                     sorted([MOCK / "manifest_2026-07-17.csv",
                             MOCK / "carrier_rates_2026-07b.csv"],
                            key=lambda p: p.name.casefold()))
    assert rr.ok, f"artifact crashed on unseen data:\n{rr.stderr}"
    produced = Path(rr.produced_path).read_bytes()
    reference = (MOCK / "_reference_summary_17.07.csv").read_bytes()
    assert produced == reference, (
        "byte mismatch on unseen data — the loop memorised Tuesday.\n"
        f"produced:\n{produced.decode(errors='replace')}\n"
        f"reference:\n{reference.decode(errors='replace')}")


def test_artifact_dir_complete_and_guard_green():
    for f in ["tool.py", "requirements.txt", "spec.json", "guard.json"]:
        assert (ARTIFACT / f).exists(), f"artifact missing {f}"
    assert (ARTIFACT / "requirements.txt").read_text().strip() == "pandas==2.2.3"
    guard = json.loads((ARTIFACT / "guard.json").read_text())
    assert guard["pass"] is True
    assert guard["network_calls"] == 0 and guard["model_calls"] == 0

    # validate against the shared contract
    spec = importlib.util.spec_from_file_location("api_schemas",
                                                  REPO / "api" / "schemas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.GuardReport.model_validate(guard)
