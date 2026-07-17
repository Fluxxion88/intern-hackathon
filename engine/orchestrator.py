"""engine/orchestrator.py — the loop itself, and termination.

PERFECT  score >= 0.99
PLATEAU  best hasn't improved by >= PLATEAU_DELTA for PLATEAU_PATIENCE
         consecutive attempts (and n >= 3)
BUDGET   n >= MAX_ATTEMPTS or elapsed >= WALL_CLOCK_MS
FAILED   terminal with best < 0.4, anti-cheat tripped twice, or spec contradiction

Never discard the best: the shipped artifact is always the best-so-far.
"""
from __future__ import annotations

import importlib.util
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import codegen, events, repairer
from .llm import LLM
from .runner import run as sandbox_run
from .scorer import Finding, ScoreResult, crash_result, score_files

REPO_ROOT = Path(__file__).resolve().parents[1]

MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "6"))
WALL_CLOCK_MS = int(os.environ.get("WALL_CLOCK_MS", "180000"))
PLATEAU_DELTA = float(os.environ.get("PLATEAU_DELTA", "0.02"))
PLATEAU_PATIENCE = int(os.environ.get("PLATEAU_PATIENCE", "2"))


def _load_guard():
    path = REPO_ROOT / "guards" / "no_llm_at_runtime.py"
    spec = importlib.util.spec_from_file_location("no_llm_at_runtime", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@dataclass
class AttemptRecord:
    n: int
    code: str
    score: float
    result: ScoreResult
    headline: str
    changed: str
    duration_ms: int


def train(job_dir: str | Path, spec: dict, input_paths: list[str | Path],
          expected_path: str | Path, llm: LLM,
          emit: events.Emitter = events.stdout_emitter) -> dict:
    """Run the loop. Returns {outcome, best, attempts, ms, artifact_dir}."""
    job_dir = Path(job_dir)
    attempts_dir = job_dir / "attempts"
    artifact_dir = job_dir / "artifact"
    attempts_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    guard_mod = _load_guard()
    expected_df = pd.read_csv(expected_path, dtype=str, keep_default_na=False)

    t0 = time.monotonic()
    attempts: list[AttemptRecord] = []
    best: AttemptRecord | None = None
    no_gain = 0
    cheat_strikes = 0
    outcome: str | None = None
    fail_reason, fail_hint = "", ""

    def elapsed_ms() -> int:
        return int((time.monotonic() - t0) * 1000)

    n = 0
    while True:
        n += 1
        emit(events.attempt_started(n))
        a_start = time.monotonic()

        # ---- WRITING / FIXING: get code ---------------------------------
        emit(events.phase("WRITING" if n == 1 else "FIXING"))
        try:
            if n == 1:
                code, headline = codegen.generate(llm, spec, input_paths)
                changed = "wrote the first version"
            else:
                src = best if best is not None else attempts[-1]
                code, changed, headline = repairer.repair(
                    llm, spec, src.code, src.result.findings)
                if code is None:
                    # rule 5: a finding contradicts the spec — human wins
                    outcome = "FAILED"
                    fail_reason = "spec_contradiction"
                    fail_hint = headline
                    break
        except Exception as exc:
            emit(events.log(f"llm error on attempt {n}: {exc}"))
            outcome = "FAILED"
            fail_reason = "llm_error"
            fail_hint = str(exc)
            break

        # ---- anti-cheat: enforced in code, not in the prompt ------------
        violation = repairer.rejects_hardcoding(code, expected_df, input_paths, spec)
        if violation:
            emit(events.log(f"anti-cheat: {violation} — re-prompting once"))
            cheat_strikes += 1
            if cheat_strikes >= 2:
                outcome = "FAILED"
                fail_reason = "anti_cheat"
                fail_hint = violation
                break
            src_code = code
            src_findings = (best.result.findings if best else [])
            code, changed, headline = repairer.repair(
                llm, spec, src_code, src_findings, violation=violation)
            if code is None or repairer.rejects_hardcoding(
                    code, expected_df, input_paths, spec):
                outcome = "FAILED"
                fail_reason = "anti_cheat"
                fail_hint = violation
                break

        code_path = attempts_dir / f"attempt_{n}.py"
        code_path.write_text(code)

        # ---- guard on every attempt: violators never get scored ---------
        guard = guard_mod.check(code_path)
        if not guard["pass"]:
            result = crash_result(expected_path, "")
            result.findings = [Finding(
                "CRASH", None, [],
                "the script was rejected before running: "
                + "; ".join(guard["violations"])
                + ". Remove every network/model/exec construct.",
                float(result.cells_total or 1))]
        else:
            # ---- RUNNING ------------------------------------------------
            emit(events.phase("RUNNING"))
            rr = sandbox_run(code_path, input_paths)
            # ---- CHECKING -----------------------------------------------
            emit(events.phase("CHECKING"))
            if rr.static_violations:
                result = crash_result(expected_path, "")
                result.findings = [Finding(
                    "CRASH", None, [],
                    "the script was rejected by the sandbox's static check: "
                    + "; ".join(rr.static_violations),
                    float(result.cells_total or 1))]
            elif not rr.ok or rr.produced_path is None:
                result = crash_result(expected_path, rr.stderr or rr.stdout)
            else:
                result = score_files(rr.produced_path, expected_path)
                out_copy = attempts_dir / f"attempt_{n}_out.csv"
                Path(rr.produced_path).replace(out_copy)

        duration_ms = int((time.monotonic() - a_start) * 1000)
        rec = AttemptRecord(n, code, result.score, result, headline, changed,
                            duration_ms)
        attempts.append(rec)
        (attempts_dir / f"attempt_{n}_findings.json").write_text(
            json.dumps(result.findings_dicts(), indent=2, ensure_ascii=False))

        emit(events.attempt_scored(
            n, result.score, result.cells_ok, result.cells_total, result.strip,
            headline, changed, duration_ms,
            datetime.now(timezone.utc).isoformat()))

        # ---- best tracking + termination --------------------------------
        prev_best = best.score if best else 0.0
        if best is None or result.score > best.score:
            best = rec
        gain = (best.score - prev_best) if attempts else 0.0
        no_gain = 0 if gain >= PLATEAU_DELTA else no_gain + 1

        if best.score >= 0.99:
            outcome = "PERFECT"
        elif no_gain >= PLATEAU_PATIENCE and n >= 3:
            outcome = "PLATEAU"
        elif n >= MAX_ATTEMPTS or elapsed_ms() >= WALL_CLOCK_MS:
            outcome = "BUDGET"
        if outcome:
            break

    # ---- terminal: freeze best, run guard, write artifact/, converge ----
    ms = elapsed_ms()
    if outcome in ("PLATEAU", "BUDGET") and (best is None or best.score < 0.4):
        outcome = "FAILED"
        fail_reason = fail_reason or "best_below_threshold"
        fail_hint = fail_hint or "the best attempt never reached 40%"

    if best is not None:
        tool_path = artifact_dir / "tool.py"
        tool_path.write_text(best.code)
        (artifact_dir / "requirements.txt").write_text("pandas==2.2.3\n")
        (artifact_dir / "spec.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False))
        guard_report = guard_mod.check(tool_path)
        (artifact_dir / "guard.json").write_text(
            json.dumps(guard_report, indent=2))

    if outcome == "FAILED":
        emit(events.failed(fail_reason, fail_hint))
    emit(events.converged(outcome, best.score if best else 0.0, len(attempts), ms))
    return {"outcome": outcome, "best": best.score if best else 0.0,
            "attempts": len(attempts), "ms": ms,
            "artifact_dir": str(artifact_dir),
            "trajectory": [a.score for a in attempts]}
