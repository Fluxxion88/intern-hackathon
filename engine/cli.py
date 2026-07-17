"""engine/cli.py — the whole loop, no web app required.

    LLM_PROVIDER=openai RECORD_CASSETTES=1 python -m engine.cli train --fixture mock/
    LLM_PROVIDER=mock python -m engine.cli train --fixture mock/   # zero network

The fixture spec is the frozen, human-approved read-back from docs/05 §4.3 —
the interview flow lives in the API; the CLI starts from the approved spec.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

# The frozen job_spec — docs/05 §4.3, verbatim. Approved read-back for the brief.
FIXTURE_SPEC = {
    "rules": [
        {"n": 1, "text": "Take two files from you: the day's manifest and the current rate card.",
         "confidence": 1.0, "source": "said"},
        {"n": 2, "text": "Throw away any run under 500 kg.",
         "confidence": 1.0, "source": "asked"},
        {"n": 3, "text": "Match each run to its truck's rate. If the truck isn't on the card, keep the run and write \"TBC\" where the cost goes.",
         "confidence": 1.0, "source": "asked"},
        {"n": 4, "text": "Work out the cost: the base fee, plus the rate per km times the distance. Round to whole dollars.",
         "confidence": 0.9, "source": "said"},
        {"n": 5, "text": "Turn kilos into tonnes, two decimal places.", "confidence": 0.85, "source": "said"},
        {"n": 6, "text": "Sort by destination A→Z, then dearest run first.", "confidence": 0.8, "source": "said"},
        {"n": 7, "text": "Name the columns your way: Date, Route, Truck, Load (t), Cost ($).", "confidence": 0.7, "source": "guessed"},
        {"n": 8, "text": "Put a TOTAL row at the bottom with the load and the cost added up, and nothing in the other columns.", "confidence": 0.9, "source": "said"}
    ],
    "guesses": [
        "Dates like 17.07.2026, because that's how your files are written.",
        "A comma in the thousands, no cents."
    ],
    "output_columns": ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
    # keep key order identical to api JobSpec.model_dump(): rules, guesses,
    # output_columns, slug — the cassette key hashes the serialized spec
    "slug": "andrei-dispatch"
}


def cmd_train(args: argparse.Namespace) -> int:
    from .llm import get_llm
    from .orchestrator import train

    fixture = Path(args.fixture)
    if not fixture.is_absolute():
        fixture = REPO_ROOT / fixture
    # canonical input order: sorted by filename (same rule as the API bridge
    # and /i/run — argv order is baked into the prompt and the trained script)
    inputs = sorted([fixture / "manifest_2026-07-14.csv",
                     fixture / "carrier_rates_2026-07.csv"],
                    key=lambda p: p.name.casefold())
    expected = fixture / "dispatch_summary_14.07.csv"
    for p in [*inputs, expected]:
        if not p.exists():
            print(f"fixture file missing: {p}", file=sys.stderr)
            return 2

    job_dir = REPO_ROOT / "data" / "jobs" / (args.job_id or "andrei-dispatch")
    llm = get_llm(args.provider)
    summary = train(job_dir, FIXTURE_SPEC, inputs, expected, llm)
    print(json.dumps({"type": "log",
                      "line": f"summary: {json.dumps(summary)}"}), flush=True)
    return 0 if summary["outcome"] != "FAILED" else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="engine.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    tr = sub.add_parser("train", help="run the training loop on a fixture")
    tr.add_argument("--fixture", required=True, help="fixture dir, e.g. mock/")
    tr.add_argument("--provider", default=None,
                    help="bedrock|anthropic|openai|mock (default: $LLM_PROVIDER)")
    tr.add_argument("--job-id", default=None)
    tr.set_defaults(fn=cmd_train)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
