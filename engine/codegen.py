"""engine/codegen.py — the first attempt. Deliberately blind to the target.

Only the scorer sees the expected file; codegen implements the spec, not the
answer. Attempt 1's ~40% is a real measurement of how underspecified natural
language is — that's the premise of the product.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .llm import LLM, parse_json_response

SYSTEM = """\
Write a standalone Python script implementing the spec below.

Signature:  python tool.py <input_a.csv> <input_b.csv> <output.csv>
Robustness: the user may pass the two input files IN EITHER ORDER. The script must
            work out which file is which by reading each file's column headers,
            never by argv position.
Allowed:    pandas, and the Python standard library. Nothing else.
Forbidden:  network of any kind, subprocess, eval/exec, reading any file that isn't
            argv[1] or argv[2], writing any file that isn't argv[3], any AI/model call.
Style:      one `run()` function, constants at the top with the same names the user
            used, a comment above each block quoting the spec rule number it
            implements. This script is shown to the person who wrote the spec — the
            comments are for them.

You do NOT get to see the target file. Implement the spec, not the answer.

Return JSON only: {"code": "<script>", "headline": "<=14 words, plain English,
what you did and what you had to guess>"}
"""


def _preview(path: str | Path, n: int = 5) -> str:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    head = df.head(n).to_csv(index=False).strip()
    return f"# {Path(path).name} ({len(df)} rows)\n{head}"


def generate(llm: LLM, spec: dict, input_paths: list[str | Path]) -> tuple[str, str]:
    """Returns (code, headline)."""
    user = (
        "THE SPEC (frozen, approved by the user):\n"
        + json.dumps({k: v for k, v in spec.items() if k != "slug"},
                     indent=2, ensure_ascii=False)  # slug is routing metadata, not a
                                                    # rule — keeping it out makes the
                                                    # cassette key slug-independent
        + "\n\nTHE INPUT FILES (first rows shown; these are the two files the "
          "script receives as argv[1] and argv[2], in this order):\n\n"
        + "\n\n".join(_preview(p) for p in input_paths)
        + "\n\nWrite the script now. Return JSON only."
    )
    raw = llm.complete(SYSTEM, [{"role": "user", "content": user}], max_tokens=8192)
    obj = parse_json_response(raw)
    return obj["code"], obj.get("headline", "Wrote a first version from your spec.")
