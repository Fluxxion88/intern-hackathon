"""engine/scorer.py — OBSERVE. The most valuable file in the repo.

Aligns columns first (set comparison), aligns rows on a discovered key,
compares cells with typed comparators, and turns every mismatch into a
deterministic, rule-inferred Finding the repairer can patch from.

score = cell_score x column_penalty x row_penalty
CRASH is a finding (score 0.0).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------- data types


@dataclass
class Finding:
    kind: str          # MISSING_COLUMN | EXTRA_COLUMN | COLUMN_NAME | ROW_COUNT | ROW_ORDER
    #                  # | UNIT | ROUNDING | DATE_FORMAT | NUMBER_FORMAT | VALUE | MISSING_ROW
    #                  # | EXTRA_ROW | TOTALS_ROW | CRASH
    column: str | None
    examples: list[tuple[str, str, str]]   # (row_key, produced, expected) — MAX 3
    hint: str          # a hypothesis, for the repairer's eyes only
    weight: float      # how many cells this explains — biggest gets fixed first

    def to_dict(self) -> dict:
        return {"kind": self.kind, "column": self.column,
                "examples": [list(e) for e in self.examples],
                "hint": self.hint, "weight": self.weight}


@dataclass
class ScoreResult:
    score: float
    cells_ok: int
    cells_total: int
    strip: str                      # one char per expected cell, row-major
    findings: list[Finding] = field(default_factory=list)

    def findings_dicts(self) -> list[dict]:
        return [f.to_dict() for f in self.findings]


# ---------------------------------------------------------------- primitives

_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")

_DATE_FORMATS = [
    ("%Y-%m-%d", "2026-07-14"),
    ("%d.%m.%Y", "14.07.2026"),
    ("%d/%m/%Y", "14/07/2026"),
    ("%m/%d/%Y", "07/14/2026"),
    ("%Y/%m/%d", "2026/07/14"),
    ("%d-%m-%Y", "14-07-2026"),
]


def _num(s: str) -> float | None:
    """Numeric value after stripping ',', '$' and spaces. None if not a number."""
    t = s.strip().replace(",", "").replace("$", "").replace(" ", "")
    if not t or not _NUM_RE.match(t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _date(s: str) -> tuple[datetime | None, str | None]:
    t = s.strip()
    for fmt, _ in _DATE_FORMATS:
        try:
            return datetime.strptime(t, fmt), fmt
        except ValueError:
            continue
    return None, None


def _canon(s: str) -> str:
    """Canonical form for key matching: numbers normalised, strings casefolded."""
    v = _num(s)
    if v is not None:
        return format(v, ".10g")
    return s.strip().casefold()


def _norm_col(name: str) -> str:
    """Aggressive column-name normalisation for mapping: casefold + alnum only."""
    return re.sub(r"[^a-z0-9]", "", name.strip().casefold())


def _empty(s: str) -> bool:
    t = s.strip()
    return t == "" or t.lower() in ("nan", "none")


def _cells_equal(p: str, e: str) -> bool:
    """Strict cell equality: exact string after strip; '' == NaN == None."""
    if _empty(p) and _empty(e):
        return True
    return p.strip() == e.strip()


def _lis_indices(seq: list[int]) -> set[int]:
    """Positions (into seq) belonging to one longest increasing subsequence."""
    if not seq:
        return set()
    n = len(seq)
    lengths = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if seq[j] < seq[i] and lengths[j] + 1 > lengths[i]:
                lengths[i] = lengths[j] + 1
                prev[i] = j
    best = max(range(n), key=lambda i: lengths[i])
    keep = set()
    while best != -1:
        keep.add(best)
        best = prev[best]
    return keep


# ---------------------------------------------------------------- column alignment


def _map_columns(prod_cols: list[str], exp_cols: list[str]):
    """Map produced -> expected columns: exact, casefold, normalised, positional.

    Returns (mapping expected->produced, missing_expected, extra_produced, renamed pairs).
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    renamed: list[tuple[str, str]] = []   # (produced_name, expected_name)

    # pass 1: exact
    for e in exp_cols:
        if e in prod_cols and e not in mapping.values():
            mapping[e] = e
            used.add(e)
    # pass 2: casefold/strip
    for e in exp_cols:
        if e in mapping:
            continue
        for p in prod_cols:
            if p in used:
                continue
            if p.strip().casefold() == e.strip().casefold():
                mapping[e] = p
                used.add(p)
                renamed.append((p, e))
                break
    # pass 3: alnum-normalised
    for e in exp_cols:
        if e in mapping:
            continue
        for p in prod_cols:
            if p in used:
                continue
            if _norm_col(p) and _norm_col(p) == _norm_col(e):
                mapping[e] = p
                used.add(p)
                renamed.append((p, e))
                break
    # pass 4: positional rescue — only when leftover counts match on both sides
    left_e = [e for e in exp_cols if e not in mapping]
    left_p = [p for p in prod_cols if p not in used]
    if left_e and len(left_e) == len(left_p):
        # keep original file order on both sides
        for e, p in zip(left_e, left_p):
            mapping[e] = p
            used.add(p)
            renamed.append((p, e))
        left_e, left_p = [], []
    missing = [e for e in exp_cols if e not in mapping]
    extra = [p for p in prod_cols if p not in used]
    return mapping, missing, extra, renamed


# ---------------------------------------------------------------- row alignment


def _find_key(exp: pd.DataFrame, prod: pd.DataFrame, mapping: dict[str, str]) -> str | None:
    """A column whose non-empty values are unique in both frames with maximal overlap."""
    best_col, best_overlap = None, 0
    for e_col, p_col in mapping.items():
        e_vals = [_canon(v) for v in exp[e_col] if not _empty(v)]
        p_vals = [_canon(v) for v in prod[p_col] if not _empty(v)]
        if not e_vals or len(set(e_vals)) != len(e_vals):
            continue
        if not p_vals or len(set(p_vals)) != len(p_vals):
            continue
        overlap = len(set(e_vals) & set(p_vals))
        if overlap > best_overlap:
            best_col, best_overlap = e_col, overlap
    if best_col is None:
        return None
    nonempty = len([v for v in exp[best_col] if not _empty(v)])
    if best_overlap >= max(2, nonempty // 2):
        return best_col
    return None


# ---------------------------------------------------------------- cell classification


def _classify_column(col: str, pairs: list[tuple[str, str, str]]) -> list[Finding]:
    """Bucket a column's mismatched cells into typed findings. Deterministic."""
    numfmt, datefmt, casef, ratio_c, rounding, value = [], [], [], [], [], []
    label = []
    for (k, p, e) in pairs:
        if _empty(p) and e.strip().casefold() == "total":
            label.append((k, p, e))
            continue
        if _empty(p) or _empty(e):
            value.append((k, p, e))
            continue
        pn, en = _num(p), _num(e)
        if pn is not None and en is not None:
            if abs(pn - en) <= 0.005:
                numfmt.append((k, p, e))
            elif abs(pn - en) <= 1.0000001:
                # off by at most one unit: a rounding-mode or
                # round-then-sum vs sum-then-round artifact
                rounding.append((k, p, e))
            else:
                ratio_c.append((k, p, e, pn, en))
            continue
        pdt, pf = _date(p)
        edt, ef = _date(e)
        if pdt is not None and edt is not None:
            if pdt == edt:
                datefmt.append((k, p, e))
            else:
                value.append((k, p, e))
            continue
        if p.strip().casefold() == e.strip().casefold():
            casef.append((k, p, e))
            continue
        value.append((k, p, e))

    findings: list[Finding] = []
    # UNIT: consistent large factor across the numeric mismatches
    if ratio_c:
        factors = [pn / en for (_, _, _, pn, en) in ratio_c if en not in (0, 0.0)]
        if len(factors) >= 2 and min(factors) > 0:
            mean_f = sum(factors) / len(factors)
            consistent = all(abs(f - mean_f) / mean_f < 0.02 for f in factors)
            if consistent and (mean_f >= 10 or mean_f <= 0.1):
                factor = 1000.0 if abs(mean_f - 1000) / 1000 < 0.02 else (
                    0.001 if abs(mean_f - 0.001) / 0.001 < 0.02 else mean_f)
                ex = [(k, p, e) for (k, p, e, _, _) in ratio_c[:3]]
                findings.append(Finding(
                    "UNIT", col, ex,
                    f"produced values are ~{factor:g}x the target in '{col}' "
                    f"(e.g. produced {ratio_c[0][1]}, expected {ratio_c[0][2]}). "
                    f"Looks like a unit conversion (kilos vs tonnes if factor is 1000). "
                    f"Match the target's decimal formatting too (e.g. '{ratio_c[0][2]}').",
                    float(len(ratio_c))))
                ratio_c = []
        if ratio_c:   # inconsistent → plain VALUE mismatches
            value.extend([(k, p, e) for (k, p, e, _, _) in ratio_c])
    if label:
        findings.append(Finding(
            "TOTALS_ROW", col, label[:3],
            f"the totals row is missing its label: the target writes 'TOTAL' in "
            f"the '{col}' column of the bottom row. That label cell is not a data "
            f"value — 'nothing in the other columns' means the columns that are "
            f"neither the label nor the summed numbers. Write the word TOTAL there.",
            float(len(label))))
    if rounding:
        findings.append(Finding(
            "ROUNDING", col, rounding[:3],
            f"values in '{col}' are off by a rounding step "
            f"(e.g. produced {rounding[0][1]}, expected {rounding[0][2]}). "
            f"Use Python's default rounding (round-half-to-even, like round() or "
            f"a plain format spec), and compute any totals from the "
            f"already-rounded per-row values.",
            float(len(rounding))))
    if numfmt:
        has_comma = any("," in e for (_, _, e) in numfmt)
        findings.append(Finding(
            "NUMBER_FORMAT", col, numfmt[:3],
            f"numbers in '{col}' are equal but written differently "
            f"(e.g. produced {numfmt[0][1]!r}, expected {numfmt[0][2]!r})."
            + (" The target uses a comma as thousands separator." if has_comma else "")
            + " Reproduce the target's exact text formatting (decimal places, separators).",
            float(len(numfmt))))
    if datefmt:
        _, pf = _date(datefmt[0][1])
        _, ef = _date(datefmt[0][2])
        findings.append(Finding(
            "DATE_FORMAT", col, datefmt[:3],
            f"same dates, different format in '{col}': produced {datefmt[0][1]!r} "
            f"({pf}), expected {datefmt[0][2]!r} ({ef}). Write dates as {ef}.",
            float(len(datefmt))))
    if casef:
        findings.append(Finding(
            "VALUE", col, casef[:3],
            f"values in '{col}' match except for letter case "
            f"(e.g. produced {casef[0][1]!r}, expected {casef[0][2]!r}). Match the case exactly.",
            float(len(casef))))
    if value:
        findings.append(Finding(
            "VALUE", col, value[:3],
            f"values in '{col}' differ from the target "
            f"(e.g. produced {value[0][1]!r}, expected {value[0][2]!r}). "
            f"Re-check the rule that fills this column.",
            float(len(value))))
    return findings


def _looks_like_totals_row(row: pd.Series, exp: pd.DataFrame, exp_cols: list[str]) -> bool:
    cells = [str(row[c]) for c in exp_cols]
    if any(c.strip().casefold() == "total" for c in cells):
        return True
    empties = sum(1 for c in cells if _empty(c))
    numerics = sum(1 for c in cells if _num(c) is not None)
    return empties >= 2 and numerics >= 1


def _totals_hint(row: pd.Series, exp: pd.DataFrame, exp_cols: list[str], row_idx) -> str:
    label_col = next((c for c in exp_cols
                      if str(row[c]).strip().casefold() == "total"), None)
    summed, empty_cols = [], []
    for c in exp_cols:
        v = _num(str(row[c]))
        if v is not None:
            others = [_num(str(x)) for i, x in exp[c].items() if i != row_idx]
            s = sum(x for x in others if x is not None)
            if abs(s - v) <= max(0.01, abs(v) * 0.001):
                summed.append(c)
        elif _empty(str(row[c])):
            empty_cols.append(c)
    parts = ["The target ends with a totals row your output is missing."]
    if label_col:
        parts.append(f"It has 'TOTAL' in the '{label_col}' column.")
    if summed:
        parts.append(f"Columns summed over the data rows: {', '.join(summed)}.")
    if empty_cols:
        parts.append(f"These columns are left empty: {', '.join(empty_cols)}.")
    parts.append("Match the target's number formatting in the totals row too.")
    return " ".join(parts)


# ---------------------------------------------------------------- main entry


def score(produced: pd.DataFrame, expected: pd.DataFrame,
          newline_mismatch: bool = False) -> ScoreResult:
    exp = expected.astype(str)
    prod = produced.astype(str)
    exp_cols = [str(c) for c in exp.columns]
    prod_cols = [str(c) for c in prod.columns]
    n_rows_e, n_cols_e = len(exp), len(exp_cols)
    cells_total = n_rows_e * n_cols_e
    findings: list[Finding] = []

    # 1. COLUMNS — set comparison first. Structure dominates everything.
    mapping, missing_cols, extra_cols, renamed = _map_columns(prod_cols, exp_cols)
    column_penalty = 1.0
    if missing_cols or extra_cols:
        column_penalty = 0.5     # brutal by design: wrong headings = a different file
    if missing_cols:
        findings.append(Finding(
            "MISSING_COLUMN", None, [("", "", c) for c in missing_cols[:3]],
            f"the target has columns your output lacks entirely: {missing_cols}. "
            f"The output must have exactly these columns, in order: {exp_cols}.",
            float(len(missing_cols) * n_rows_e)))
    if extra_cols:
        findings.append(Finding(
            "EXTRA_COLUMN", None, [("", c, "") for c in extra_cols[:3]],
            f"your output has columns the target does not: {extra_cols}. "
            f"The output must have exactly these columns, in order: {exp_cols}.",
            float(len(extra_cols) * n_rows_e)))
    if renamed:
        findings.append(Finding(
            "COLUMN_NAME", None, [("", p, e) for (p, e) in renamed[:3]],
            "column names don't match the target exactly. Rename: "
            + "; ".join(f"{p!r} -> {e!r}" for p, e in renamed)
            + f". The header must read exactly: {exp_cols}.",
            float(cells_total)))

    # 2. ROWS — align on a discovered key so a sort bug is ONE finding.
    key_col = _find_key(exp, prod, mapping) if mapping else None
    matched: list[tuple[int, int]] = []       # (exp_pos, prod_pos)
    unmatched_exp: list[int] = []
    unmatched_prod: list[int] = []
    exp_idx = list(range(len(exp)))
    prod_idx = list(range(len(prod)))

    if key_col is not None:
        p_col = mapping[key_col]
        p_lookup: dict[str, int] = {}
        for i in prod_idx:
            v = str(prod.iloc[i][p_col])
            if not _empty(v):
                p_lookup.setdefault(_canon(v), i)
        taken: set[int] = set()
        for i in exp_idx:
            v = str(exp.iloc[i][key_col])
            j = p_lookup.get(_canon(v)) if not _empty(v) else None
            if j is not None and j not in taken:
                matched.append((i, j))
                taken.add(j)
            else:
                unmatched_exp.append(i)
        unmatched_prod = [j for j in prod_idx if j not in taken]
        # similarity rescue: a row with ONE wrong cell must not read as an
        # EXTRA_ROW + MISSING_ROW pair (that invites 'the target is wrong'
        # readings). Pair leftover rows sharing >=2 cells; the differing
        # cells then become ordinary typed findings.
        if unmatched_exp and unmatched_prod:
            cand = []
            for i in unmatched_exp:
                for j in unmatched_prod:
                    sim = sum(1 for e_col, p_col in mapping.items()
                              if _cells_equal(str(prod.iloc[j][p_col]),
                                              str(exp.iloc[i][e_col])))
                    if sim >= 2:
                        cand.append((-sim, i, j))
            cand.sort()
            used_i: set[int] = set()
            used_j: set[int] = set()
            for _, i, j in cand:
                if i in used_i or j in used_j:
                    continue
                matched.append((i, j))
                used_i.add(i)
                used_j.add(j)
            unmatched_exp = [i for i in unmatched_exp if i not in used_i]
            unmatched_prod = [j for j in unmatched_prod if j not in used_j]
            matched.sort()
        # totals-row rescue: a produced totals-ish row pairs with the expected
        # totals row even when every cell disagrees — a broken totals row must
        # surface as cell findings, not as EXTRA_ROW + 'missing totals row'.
        if unmatched_exp and unmatched_prod:
            exp_tot = [i for i in unmatched_exp
                       if _looks_like_totals_row(exp.iloc[i], exp, exp_cols)]

            def _prod_totalish(j: int) -> bool:
                cells = [str(prod.iloc[j][mapping[c]])
                         for c in exp_cols if c in mapping]
                if any(c.strip().casefold() == "total" for c in cells):
                    return True
                empties = sum(1 for c in cells if _empty(c))
                numerics = sum(1 for c in cells if _num(c) is not None)
                return empties >= 2 and numerics >= 1

            prod_tot = [j for j in unmatched_prod if _prod_totalish(j)]
            for i, j in zip(exp_tot, prod_tot):
                matched.append((i, j))
                unmatched_exp.remove(i)
                unmatched_prod.remove(j)
            matched.sort()
    else:
        n = min(len(exp), len(prod))
        matched = [(i, i) for i in range(n)]
        unmatched_exp = list(range(n, len(exp)))
        unmatched_prod = list(range(n, len(prod)))
        if len(exp) != len(prod):
            findings.append(Finding(
                "ROW_COUNT", None, [("", str(len(prod)), str(len(exp)))],
                f"your output has {len(prod)} rows; the target has {len(exp)}.",
                float(abs(len(exp) - len(prod)) * n_cols_e)))

    # row order: LIS over produced indices in expected order → ONE finding
    misplaced_exp_rows: set[int] = set()
    if key_col is not None and len(matched) >= 2:
        seq = [j for (_, j) in matched]
        keep = _lis_indices(seq)
        out_positions = [idx for idx in range(len(matched)) if idx not in keep]
        if out_positions:
            misplaced_exp_rows = {matched[idx][0] for idx in out_positions}
            ex = []
            for idx in out_positions[:3]:
                i, j = matched[idx]
                ex.append((str(exp.iloc[i][key_col]),
                           f"row {j + 1} in your output", f"row {i + 1} in the target"))
            findings.append(Finding(
                "ROW_ORDER", None, ex,
                "the rows are all there but in a different order than the target. "
                "Re-check the spec's sorting rule (and where special rows like 'TBC' go).",
                float(len(out_positions) * n_cols_e)))

    # 3. CELLS — typed comparison on matched rows
    ok = [[False] * n_cols_e for _ in range(n_rows_e)]
    mismatches: dict[str, list[tuple[str, str, str]]] = {c: [] for c in exp_cols}
    for (i, j) in matched:
        row_key = str(exp.iloc[i][key_col]) if key_col else f"row {i + 1}"
        for ci, e_col in enumerate(exp_cols):
            p_col = mapping.get(e_col)
            if p_col is None:
                continue
            e_val = str(exp.iloc[i][e_col])
            p_val = str(prod.iloc[j][p_col])
            equal = _cells_equal(p_val, e_val)
            if equal:
                ok[i][ci] = i not in misplaced_exp_rows
            else:
                mismatches[e_col].append((row_key, p_val.strip(), e_val.strip()))

    for e_col in exp_cols:
        if mismatches[e_col]:
            findings.extend(_classify_column(e_col, mismatches[e_col]))

    # 4. unmatched expected rows → TOTALS_ROW or MISSING_ROW
    totals_rows = [i for i in unmatched_exp
                   if _looks_like_totals_row(exp.iloc[i], exp, exp_cols)]
    missing_rows = [i for i in unmatched_exp if i not in totals_rows]
    for i in totals_rows:
        findings.append(Finding(
            "TOTALS_ROW", None,
            [(f"row {i + 1}", "<absent>",
              ",".join(str(exp.iloc[i][c]) for c in exp_cols))],
            _totals_hint(exp.iloc[i], exp, exp_cols, exp.index[i]),
            float(n_cols_e)))
    if missing_rows:
        ex = [(f"row {i + 1}", "<absent>",
               ",".join(str(exp.iloc[i][c]) for c in exp_cols))
              for i in missing_rows[:3]]
        findings.append(Finding(
            "MISSING_ROW", None, ex,
            "the target has rows your output is missing. Re-check joins and "
            "filters — rows must not be dropped unless a spec rule says so. "
            "The spec is correct; do not conclude the target is wrong.",
            float(len(missing_rows) * n_cols_e)))
    if unmatched_prod:
        ex = [(f"row {j + 1}",
               ",".join(str(prod.iloc[j][mapping.get(c, prod_cols[0])])
                        for c in exp_cols if c in mapping), "<not in target>")
              for j in unmatched_prod[:3]]
        findings.append(Finding(
            "EXTRA_ROW", None, ex,
            "your output keeps rows the target drops. The spec likely has a "
            "filter rule (e.g. a minimum size) that these rows fail. The spec "
            "is correct; do not conclude the target is wrong.",
            float(len(unmatched_prod) * n_cols_e)))

    # newline style is part of byte-equality; surface it once, gently
    if newline_mismatch:
        findings.append(Finding(
            "VALUE", None, [],
            "line endings differ: the target file uses Windows-style '\\r\\n'. "
            "Write the CSV with lineterminator='\\r\\n'.",
            1.0))

    # 5. the number
    cells_ok = sum(1 for r in ok for c in r if c)
    cell_score = cells_ok / cells_total if cells_total else 0.0
    rp_max = max(len(prod), n_rows_e)
    row_penalty = (min(len(prod), n_rows_e) / rp_max) if rp_max else 0.0
    final = cell_score * column_penalty * row_penalty
    # renames and newline style don't zero cells, but they block PERFECT:
    if renamed or newline_mismatch:
        final = min(final, 0.98)
    strip = "".join("1" if c else "0" for r in ok for c in r)

    findings.sort(key=lambda f: (-f.weight, f.kind, f.column or ""))
    return ScoreResult(round(final, 4), cells_ok, cells_total, strip, findings)


def crash_result(expected_path: str | Path, traceback_text: str) -> ScoreResult:
    """Traceback → CRASH finding, score 0.0, loop continues."""
    try:
        exp = pd.read_csv(expected_path, dtype=str, keep_default_na=False)
        cells_total = len(exp) * len(exp.columns)
    except Exception:
        cells_total = 0
    tail = "\n".join(traceback_text.strip().splitlines()[-15:])
    f = Finding("CRASH", None, [], f"the script crashed. Last lines:\n{tail}",
                float(cells_total or 1))
    return ScoreResult(0.0, 0, cells_total, "0" * cells_total, [f])


def _newline_style(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return "\r\n" if b"\r\n" in data else "\n"


def score_files(produced_path: str | Path, expected_path: str | Path) -> ScoreResult:
    try:
        prod = pd.read_csv(produced_path, dtype=str, keep_default_na=False)
    except Exception as exc:  # unreadable output is a crash-grade finding
        return crash_result(expected_path, f"could not read produced CSV: {exc}")
    exp = pd.read_csv(expected_path, dtype=str, keep_default_na=False)
    nl_mismatch = _newline_style(produced_path) != _newline_style(expected_path)
    return score(prod, exp, newline_mismatch=nl_mismatch)
