"""engine/repairer.py — SELF-CORRECT: findings -> patch + plain-language line.

Anti-cheat (§6.2) is enforced in code, not in the prompt: distinctive literals
from the target file appearing in generated code mean the attempt is discarded.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from .llm import LLM, parse_json_response
from .scorer import Finding

SYSTEM = """\
You are fixing a Python script so its output matches a target file exactly.

You get: the frozen spec (approved by the user — TREAT AS LAW), the current script,
and a list of findings from a deterministic diff. The findings are FACTS, not
opinions. Do not re-derive them. Do not question them.

Return JSON only:
{
  "code":     "<the complete corrected script>",
  "changed":  "<what you changed, <=6 words, e.g. 'rounding on the Cost column'>",
  "headline": "<what a non-technical person would understand, <=14 words, plain
               English, no jargon: 'Sorted the rows the way you asked. One cost
               is a dollar off.'>"
}

Rules:
1. Fix the HIGHEST-WEIGHT finding first. One structural fix beats five cosmetic ones.
2. Never fix a finding by hard-coding expected values. If you write a literal from
   the target file into the script, you have cheated and the tool is worthless on
   tomorrow's data. This is the only unforgivable error.
3. Never add a dependency. pandas and the stdlib. Nothing else.
4. Never make a network call, import requests/urllib/socket/httpx, or call a model.
5. If a finding contradicts the spec, DO NOT change the code — set
   "code": null and explain in "headline". The human's spec wins over your reading
   of the diff, and a human will be told.
6. The headline is read by a dispatch manager, not an engineer. "Fixed the unit
   conversion" — no. "It was writing kilos where you wanted tonnes" — yes.
"""

_COMMON_WORDS = {"total", "date", "route", "truck", "load", "cost", "none",
                 "true", "false", "null", "usd"}


def distinctive_values(expected: pd.DataFrame, input_paths: list[str | Path],
                       spec: dict | None = None) -> set[str]:
    """Cell values from the target that appear nowhere legitimate: not in the
    inputs, not in the spec the human approved, not trivial words."""
    corpus = ""
    for p in input_paths:
        corpus += Path(p).read_text()
    if spec is not None:
        corpus += json.dumps(spec, ensure_ascii=False)
    out: set[str] = set()
    for col in expected.columns:
        for v in expected[col].astype(str):
            v = v.strip()
            if len(v) <= 3 or v.casefold() in _COMMON_WORDS:
                continue
            if v in corpus:
                continue
            out.add(v)
    return out


def rejects_hardcoding(code: str, expected: pd.DataFrame,
                       input_paths: list[str | Path],
                       spec: dict | None = None) -> str | None:
    """>=2 distinctive target literals verbatim in the source => cheating."""
    literals = distinctive_values(expected, input_paths, spec)
    hits = sorted(v for v in literals
                  if repr(v) in code or f'"{v}"' in code or f"'{v}'" in code)
    if len(hits) >= 2:
        return f"hardcoded target values: {hits[:3]}"
    return None


def _findings_block(findings: list[Finding]) -> str:
    lines = []
    for f in sorted(findings, key=lambda f: (-f.weight, f.kind, f.column or "")):
        lines.append(json.dumps({
            "kind": f.kind, "column": f.column, "weight": f.weight,
            "examples": [{"row": k, "produced": p, "expected": e}
                         for (k, p, e) in f.examples],
            "hint": f.hint,
        }, ensure_ascii=False))
    return "\n".join(lines)


def repair(llm: LLM, spec: dict, code: str, findings: list[Finding],
           violation: str | None = None,
           nudge: str | None = None) -> tuple[str | None, str, str]:
    """Returns (code_or_None, changed, headline). code None = spec contradiction."""
    user = (
        "THE FROZEN SPEC (LAW):\n"
        + json.dumps({k: v for k, v in spec.items() if k != "slug"},
                     indent=2, ensure_ascii=False)  # slug excluded: cassette key
                                                    # must not depend on it
        + "\n\nTHE CURRENT SCRIPT:\n```python\n" + code + "\n```\n"
        + "\nFINDINGS from the deterministic diff (facts, heaviest first):\n"
        + _findings_block(findings)
    )
    if violation:
        user += (
            "\n\nYOUR PREVIOUS FIX WAS REJECTED by the anti-cheat check: "
            + violation
            + "\nYou copied values from the target file into the script. Remove them; "
              "compute every value from the inputs and the spec's rules only."
        )
    if nudge:
        user += "\n\nNOTE: " + nudge
    user += "\n\nReturn JSON only."
    raw = llm.complete(SYSTEM, [{"role": "user", "content": user}], max_tokens=8192)
    obj = parse_json_response(raw)
    return (obj.get("code"),
            obj.get("changed", "a fix"),
            obj.get("headline", "Made a fix based on the differences."))
