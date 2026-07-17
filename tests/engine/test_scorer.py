"""GATE 1 — the scorer, tested against a hand-broken tool.py.

The broken tool is a plausible 'attempt 1': wrong column names, kilos not
tonnes, small runs kept, no totals row, ISO dates. Against the 14.07 ground
truth it must score ~0.41 (accept 0.35-0.47), matching the attempt-1 profile
in docs/06-MOCK-DATA.md §6.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from engine import scorer
from engine.scorer import score, score_files, crash_result

REPO = Path(__file__).resolve().parents[2]
MOCK = REPO / "mock"
EXPECTED = MOCK / "dispatch_summary_14.07.csv"

# Hand-broken attempt 1: wrong column names, kilos not tonnes, small runs
# kept, no totals row, ISO dates. Join, TBC handling, rounding and comma
# formatting are right — that's what a competent-but-underspecified first
# attempt looks like.
BROKEN_TOOL = '''\
import sys
import pandas as pd

def run(manifest_path, rates_path, out_path):
    m = pd.read_csv(manifest_path)
    r = pd.read_csv(rates_path)
    df = m.merge(r, on="carrier_code", how="left")
    cost = (df["base_fee_usd"] + df["rate_per_km_usd"] * df["distance_km"]).round(0)
    df["truck"] = df["truck_id"].fillna("TBC")
    df["cost_num"] = cost
    df["cost_out"] = [
        "TBC" if t == "TBC" else f"{int(c):,}" for t, c in zip(df["truck"], cost)
    ]
    out = pd.DataFrame({
        "date": df["date"],                    # ISO, as in the manifest (wrong)
        "route": df["destination"],
        "truck": df["truck"],
        "weight_kg": df["weight_kg"],          # kilos (wrong), wrong name
        "cost_usd": df["cost_out"],            # wrong name
    })
    sort_cost = df["cost_num"].fillna(-1)
    out = out.assign(_c=-sort_cost.values).sort_values(
        ["route", "_c"], kind="mergesort").drop(columns="_c")
    out.to_csv(out_path, index=False)

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
'''


def _run_tool(code: str, tmp_path: Path, inputs=None) -> Path:
    tool = tmp_path / "tool.py"
    tool.write_text(code)
    out = tmp_path / "out.csv"
    inputs = inputs or [MOCK / "manifest_2026-07-14.csv", MOCK / "carrier_rates_2026-07.csv"]
    subprocess.run([sys.executable, str(tool), str(inputs[0]), str(inputs[1]), str(out)],
                   check=True, capture_output=True, timeout=60)
    return out


# ------------------------------------------------------------------ THE GATE

def test_broken_tool_scores_about_0_41(tmp_path):
    out = _run_tool(BROKEN_TOOL, tmp_path)
    res = score_files(out, EXPECTED)
    assert 0.35 <= res.score <= 0.47, f"gate: expected ~0.41, got {res.score}"
    assert res.cells_total == 50
    assert len(res.strip) == 50
    kinds = {f.kind for f in res.findings}
    # the attempt-1 profile from docs/06 §6
    assert "COLUMN_NAME" in kinds
    assert "UNIT" in kinds
    assert "EXTRA_ROW" in kinds
    assert "TOTALS_ROW" in kinds
    assert "DATE_FORMAT" in kinds
    unit = next(f for f in res.findings if f.kind == "UNIT")
    assert unit.column == "Load (t)"
    assert "1000" in unit.hint
    extra = next(f for f in res.findings if f.kind == "EXTRA_ROW")
    assert extra.weight == 4 * 5   # the 4 small runs
    # findings carry at most 3 examples and are sorted heaviest-first
    assert all(len(f.examples) <= 3 for f in res.findings)
    weights = [f.weight for f in res.findings]
    assert weights == sorted(weights, reverse=True)


def test_broken_tool_findings_are_deterministic(tmp_path):
    out = _run_tool(BROKEN_TOOL, tmp_path)
    a = score_files(out, EXPECTED)
    b = score_files(out, EXPECTED)
    assert a.score == b.score
    assert a.strip == b.strip
    assert [f.to_dict() for f in a.findings] == [f.to_dict() for f in b.findings]


# ------------------------------------------------------------- unit behaviour

def test_perfect_copy_scores_1(tmp_path):
    exp = pd.read_csv(EXPECTED, dtype=str, keep_default_na=False)
    res = score(exp.copy(), exp)
    assert res.score == 1.0
    assert res.strip == "1" * 50
    assert res.findings == []


def test_newline_mismatch_blocks_perfect(tmp_path):
    # cell-identical but LF endings while target is CRLF
    exp = pd.read_csv(EXPECTED, dtype=str, keep_default_na=False)
    p = tmp_path / "p.csv"
    exp.to_csv(p, index=False, lineterminator="\n")
    res = score_files(p, EXPECTED)
    assert res.score <= 0.98
    assert any("\\r\\n" in f.hint for f in res.findings)
    # and CRLF output reaches 1.0
    p2 = tmp_path / "p2.csv"
    exp.to_csv(p2, index=False, lineterminator="\r\n")
    assert score_files(p2, EXPECTED).score == 1.0


def test_sort_bug_yields_one_row_order_finding():
    exp = pd.read_csv(EXPECTED, dtype=str, keep_default_na=False)
    shuffled = exp.iloc[[3, 0, 5, 2, 8, 1, 6, 4, 7, 9]].reset_index(drop=True)
    res = score(shuffled, exp)
    row_order = [f for f in res.findings if f.kind == "ROW_ORDER"]
    assert len(row_order) == 1, "a sort bug must be ONE finding, not 50 cell errors"
    # no cell VALUE noise: the values are all present and matched by key
    assert not [f for f in res.findings if f.kind == "VALUE" and f.examples]
    assert res.score < 0.99  # wrong order can't be declared PERFECT


def test_wrong_column_set_is_penalised_half():
    exp = pd.read_csv(EXPECTED, dtype=str, keep_default_na=False)
    prod = exp.copy().drop(columns=["Truck"])
    prod["completely_new"] = "x"
    prod["another_new"] = "y"
    res = score(prod, exp)
    assert any(f.kind == "MISSING_COLUMN" for f in res.findings)
    assert any(f.kind == "EXTRA_COLUMN" for f in res.findings)
    assert res.score <= 0.5


def test_number_format_comma_detected():
    exp = pd.read_csv(EXPECTED, dtype=str, keep_default_na=False)
    prod = exp.copy()
    prod["Cost ($)"] = [v.replace(",", "") for v in prod["Cost ($)"]]
    res = score(prod, exp)
    nf = [f for f in res.findings if f.kind == "NUMBER_FORMAT"]
    assert len(nf) == 1 and nf[0].column == "Cost ($)"
    assert "comma" in nf[0].hint
    assert res.score < 1.0


def test_rounding_detected():
    exp = pd.read_csv(EXPECTED, dtype=str, keep_default_na=False)
    prod = exp.copy()
    prod.loc[7, "Cost ($)"] = "362.4"   # rounds to 362
    res = score(prod, exp)
    assert any(f.kind == "ROUNDING" and f.column == "Cost ($)" for f in res.findings)


def test_empty_equals_nan():
    exp = pd.DataFrame({"a": ["", "x"], "b": ["1", "2"]})
    prod = pd.DataFrame({"a": [float("nan"), "x"], "b": ["1", "2"]})
    res = score(prod, exp)
    assert res.score == 1.0


def test_crash_is_a_finding():
    res = crash_result(EXPECTED, "Traceback...\nKeyError: 'weight_kg'")
    assert res.score == 0.0
    assert res.strip == "0" * 50
    assert res.findings[0].kind == "CRASH"
    assert "KeyError" in res.findings[0].hint


def test_numeric_comparator_strips_currency():
    assert scorer._num("$1,123") == 1123
    assert scorer._num(" 4 180 ") == 4180
    assert scorer._num("TBC") is None
