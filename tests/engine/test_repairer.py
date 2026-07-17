"""Anti-cheat: distinctive target literals in generated code => rejection."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.repairer import distinctive_values, rejects_hardcoding

REPO = Path(__file__).resolve().parents[2]
MOCK = REPO / "mock"
INPUTS = [MOCK / "manifest_2026-07-14.csv", MOCK / "carrier_rates_2026-07.csv"]
EXPECTED = pd.read_csv(MOCK / "dispatch_summary_14.07.csv",
                       dtype=str, keep_default_na=False)
SPEC = {"output_columns": ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
        "rules": [{"text": "write TBC where the cost goes"}]}


def test_distinctive_values_excludes_inputs_and_spec():
    vals = distinctive_values(EXPECTED, INPUTS, SPEC)
    # computed costs & the reformatted dates are distinctive…
    assert "1,123" in vals
    assert "14.07.2026" in vals
    # …but values visible in the inputs or the spec are not
    assert "TRK-22" not in vals      # in the rate card
    assert "Bakersfield" not in vals  # in the manifest
    assert "TBC" not in vals          # in the spec


def test_honest_code_is_accepted():
    code = (
        "import sys\nimport pandas as pd\n"
        "m = pd.read_csv(sys.argv[1]); r = pd.read_csv(sys.argv[2])\n"
        "df = m.merge(r, on='carrier_code', how='left')\n"
        "df['cost'] = df['base_fee_usd'] + df['rate_per_km_usd'] * df['distance_km']\n"
        "df.to_csv(sys.argv[3], index=False)\n")
    assert rejects_hardcoding(code, EXPECTED, INPUTS, SPEC) is None


def test_memorised_answers_are_rejected():
    code = (
        "import sys, pandas as pd\n"
        "rows = [['14.07.2026', 'Bakersfield', 'TRK-22', '3.15', '1,123'],\n"
        "        ['14.07.2026', 'Bakersfield', 'TRK-15', '1.78', '942']]\n"
        "pd.DataFrame(rows).to_csv(sys.argv[3], index=False)\n")
    violation = rejects_hardcoding(code, EXPECTED, INPUTS, SPEC)
    assert violation is not None
    assert "hardcoded" in violation
