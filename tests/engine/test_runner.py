"""Sandbox runner: static check, isolation, execution, crash capture."""
from __future__ import annotations

from pathlib import Path

from engine.runner import run, static_check

REPO = Path(__file__).resolve().parents[2]
MOCK = REPO / "mock"
INPUTS = [MOCK / "manifest_2026-07-14.csv", MOCK / "carrier_rates_2026-07.csv"]

OK_SCRIPT = """\
import sys
import pandas as pd
m = pd.read_csv(sys.argv[1])
m.head(3).to_csv(sys.argv[3], index=False)
"""


def test_static_check_bans_network_and_exec():
    assert static_check("import requests") != []
    assert static_check("from urllib.request import urlopen") != []
    assert static_check("import subprocess") != []
    assert static_check("eval('1+1')") != []
    assert static_check("exec('x=1')") != []
    assert static_check("import socket") != []
    assert static_check("import os\nos.system('ls')") != []
    assert static_check("open('/etc/passwd', 'w')") != []
    assert static_check(OK_SCRIPT) == []


def test_runner_executes_pandas_script(tmp_path):
    s = tmp_path / "tool.py"
    s.write_text(OK_SCRIPT)
    rr = run(s, INPUTS)
    assert rr.ok, rr.stderr
    assert rr.produced_path is not None and Path(rr.produced_path).exists()
    assert rr.duration_ms >= 0


def test_runner_blocks_banned_script_before_running(tmp_path):
    s = tmp_path / "tool.py"
    s.write_text("import requests\nprint('never runs')")
    rr = run(s, INPUTS)
    assert not rr.ok
    assert rr.static_violations


def test_runner_captures_traceback(tmp_path):
    s = tmp_path / "tool.py"
    s.write_text("import sys\nimport pandas as pd\nraise KeyError('weight_kg')")
    rr = run(s, INPUTS)
    assert not rr.ok
    assert "KeyError" in rr.stderr


def test_runner_env_is_empty(tmp_path):
    s = tmp_path / "tool.py"
    s.write_text(
        "import os, sys\n"
        "assert 'OPENAI_API_KEY' not in os.environ, 'secret leaked'\n"
        "assert 'ANTHROPIC_API_KEY' not in os.environ\n"
        "open(sys.argv[3], 'x').write('a\\n1\\n') if False else None\n"
        "import pandas as pd\n"
        "pd.DataFrame({'a':[1]}).to_csv(sys.argv[3], index=False)\n"
    )
    rr = run(s, INPUTS)
    assert rr.ok, rr.stderr
