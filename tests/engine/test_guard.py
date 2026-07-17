"""Guard: no LLM at runtime, output shape matches api/schemas.py GuardReport."""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load("no_llm_at_runtime", REPO / "guards" / "no_llm_at_runtime.py")
schemas = _load("api_schemas", REPO / "api" / "schemas.py")


def test_clean_pandas_script_passes(tmp_path):
    p = tmp_path / "tool.py"
    p.write_text(
        "import sys\nimport pandas as pd\n"
        "def run(a, b, o):\n    pd.read_csv(a).to_csv(o, index=False)\n"
        "run(sys.argv[1], sys.argv[2], sys.argv[3])\n")
    rep = guard.check(p)
    assert rep["pass"] is True
    assert rep["network_calls"] == 0
    assert rep["model_calls"] == 0
    assert rep["violations"] == []


def test_model_import_fails(tmp_path):
    p = tmp_path / "tool.py"
    p.write_text("import openai\nimport requests\n")
    rep = guard.check(p)
    assert rep["pass"] is False
    assert rep["model_calls"] >= 1
    assert rep["network_calls"] >= 1


def test_url_and_eval_fail(tmp_path):
    p = tmp_path / "tool.py"
    p.write_text("u = 'https://api.example.com'\neval('1')\n")
    rep = guard.check(p)
    assert rep["pass"] is False
    assert rep["network_calls"] >= 1


def test_report_matches_guardreport_schema(tmp_path):
    p = tmp_path / "tool.py"
    p.write_text("import pandas as pd\n")
    rep = guard.check(p)
    parsed = schemas.GuardReport.model_validate(rep)   # 'pass' alias must work
    assert parsed.pass_ is True
    assert parsed.checked_at
