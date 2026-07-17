"""guards/no_llm_at_runtime.py — the claim, enforced.

Static proof that a trained artifact contains no model calls and no network.
Its JSON output renders the "No AI inside" card and must match GuardReport
in api/schemas.py: {pass, network_calls, model_calls, checked_at, violations}.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BANNED_IMPORTS = {"anthropic", "openai", "boto3", "requests", "httpx", "urllib",
                  "socket", "aiohttp", "openai_agents", "langchain", "litellm"}
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "system", "popen"}

MODEL_LIBS = {"anthropic", "openai", "boto3", "openai_agents", "langchain", "litellm"}
NETWORK_LIBS = {"requests", "httpx", "urllib", "socket", "aiohttp"}

URL_RE = re.compile(r"https?://")
KEY_RE = re.compile(r"sk-[A-Za-z0-9_\-]{20,}")


def check(path: str | Path) -> dict:
    source = Path(path).read_text()
    violations: list[str] = []
    network_calls = 0
    model_calls = 0

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"pass": False, "network_calls": 0, "model_calls": 0,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "violations": [f"syntax error: {exc}"]}

    for node in ast.walk(tree):
        mods: list[str] = []
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [(node.module or "").split(".")[0]]
        for mod in mods:
            if mod in BANNED_IMPORTS:
                violations.append(f"banned import: {mod}")
                if mod in MODEL_LIBS:
                    model_calls += 1
                if mod in NETWORK_LIBS:
                    network_calls += 1
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in BANNED_CALLS:
                violations.append(f"banned call: {name}()")

    for m in URL_RE.finditer(source):
        network_calls += 1
        violations.append(f"URL literal at offset {m.start()}")
    for _ in KEY_RE.finditer(source):
        violations.append("something that looks like an API key")

    return {
        "pass": not violations,
        "network_calls": network_calls,
        "model_calls": model_calls,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "violations": violations,
    }


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), indent=2))
