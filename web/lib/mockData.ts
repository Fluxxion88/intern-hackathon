// DEMO INSURANCE — fixture data used when NEXT_PUBLIC_MOCK=1 or the API is unreachable.
// Copy here mirrors docs/03-SCREENS.md and mock/ verbatim. Do not rewrite it.

import type { FilePreview, GuardReport, JobSpec, Question } from "./types";

export const MOCK_JOB_ID = "demo";
export const MOCK_SLUG = "andrei-dispatch";

/** Inlined from mock/brief.json — the "Use the freight example" button. */
export const FREIGHT_BRIEF =
  "Every morning I get the manifest for the day and the rate card from accounts. I put them together into one summary for the drivers — my columns, my order. Loads in tonnes not kilos because nobody thinks in kilos. Work out the cost per run, that's the base fee plus the per-km rate times how far it's going. Total at the bottom. Skip the little stuff, under half a tonne isn't worth the diesel. Takes me forty minutes and I've been doing it since 2019.";

export const MOCK_QUESTIONS: Question[] = [
  {
    id: "q1",
    question: 'What counts as "little stuff"?',
    why: "You said to skip it, and I don't want to throw away a run you wanted kept — or keep one you didn't.",
    suggestions: ["Under 500 kg", "Under half a tonne exactly"],
  },
  {
    id: "q2",
    question: "If a truck isn't on the rate card, what do I do with that run?",
    why: "I need this because I can't work out a cost without a rate, and I'd rather ask than guess and be wrong every morning.",
    suggestions: ["Leave it out", 'Keep it, mark the cost as "TBC"'],
  },
  {
    id: "q3",
    question: "What should I call the file I give you back?",
    why: "You'll be looking for it every morning, so it should be named the way you'd name it.",
    suggestions: ["Name it with the date, like the summary I'm giving you"],
  },
];

export const MOCK_SPEC: JobSpec = {
  rules: [
    { n: 1, text: "Take two files from you: the day's manifest and the current rate card.", confidence: 0.98, source: "said" },
    { n: 2, text: "Throw away any run under 500 kg.", confidence: 0.95, source: "asked" },
    { n: 3, text: 'Match each run to its truck\'s rate. If the truck isn\'t on the card, keep the run and write "TBC" where the cost goes.', confidence: 0.95, source: "asked" },
    { n: 4, text: "Work out the cost: the base fee, plus the rate per km times the distance. Round to whole dollars.", confidence: 0.92, source: "said" },
    { n: 5, text: "Turn kilos into tonnes, two decimal places.", confidence: 0.94, source: "said" },
    { n: 6, text: "Sort by destination A→Z, then dearest run first.", confidence: 0.85, source: "guessed" },
    { n: 7, text: "Name the columns your way: Date, Route, Truck, Load (t), Cost ($).", confidence: 0.9, source: "said" },
    { n: 8, text: "Put a TOTAL row at the bottom with the load and the cost added up, and nothing in the other columns.", confidence: 0.93, source: "said" },
  ],
  guesses: [
    "Dates like 17.07.2026, because that's how your files are written.",
    "A comma in the thousands, no cents.",
  ],
  output_columns: ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
  slug: MOCK_SLUG,
};

/** First rows of mock/dispatch_summary_14.07.csv — the expected file. */
export const MOCK_EXPECTED_PREVIEW: FilePreview = {
  columns: ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
  rows: [
    ["14.07.2026", "Bakersfield", "TRK-22", "3.15", "1,123"],
    ["14.07.2026", "Bakersfield", "TRK-15", "1.78", "942"],
    ["14.07.2026", "Fresno", "TRK-09", "4.02", "1,007"],
    ["14.07.2026", "Fresno", "TRK-11", "1.24", "940"],
    ["14.07.2026", "Fresno", "TRK-22", "1.59", "684"],
  ],
  truncated: true,
};

export const MOCK_EXPECTED_FULL: FilePreview = {
  columns: ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
  rows: [
    ["14.07.2026", "Bakersfield", "TRK-22", "3.15", "1,123"],
    ["14.07.2026", "Bakersfield", "TRK-15", "1.78", "942"],
    ["14.07.2026", "Fresno", "TRK-09", "4.02", "1,007"],
    ["14.07.2026", "Fresno", "TRK-11", "1.24", "940"],
    ["14.07.2026", "Fresno", "TRK-22", "1.59", "684"],
    ["14.07.2026", "Fresno", "TRK-03", "2.90", "628"],
    ["14.07.2026", "Modesto", "TRK-07", "0.94", "383"],
    ["14.07.2026", "Sacramento", "TRK-07", "0.86", "362"],
    ["14.07.2026", "Sacramento", "TBC", "2.26", "TBC"],
    ["", "", "TOTAL", "18.74", "6,069"],
  ],
  truncated: false,
};

/** Attempt-4 diff: one cost a dollar off, plus rounding drift — for [ see the diff ]. */
export const MOCK_DIFF = {
  expected: MOCK_EXPECTED_FULL,
  produced: {
    columns: ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
    rows: [
      ["14.07.2026", "Bakersfield", "TRK-22", "3.15", "1,123"],
      ["14.07.2026", "Bakersfield", "TRK-15", "1.78", "941"],
      ["14.07.2026", "Fresno", "TRK-09", "4.02", "1,007"],
      ["14.07.2026", "Fresno", "TRK-11", "1.24", "940"],
      ["14.07.2026", "Fresno", "TRK-22", "1.59", "684"],
      ["14.07.2026", "Fresno", "TRK-03", "2.90", "628"],
      ["14.07.2026", "Modesto", "TRK-07", "0.94", "383"],
      ["14.07.2026", "Sacramento", "TRK-07", "0.86", "362"],
      ["14.07.2026", "Sacramento", "TBC", "2.26", "TBC"],
      ["", "", "TOTAL", "18.74", "6,068"],
    ],
    truncated: false,
  } as FilePreview,
  wrong_cells: [
    [1, 4],
    [9, 4],
  ] as [number, number][],
};

/** The result of a run on /i/[slug] in mock mode — mock/_reference_summary_17.07.csv. */
export const MOCK_RUN_RESULT: FilePreview = {
  columns: ["Date", "Route", "Truck", "Load (t)", "Cost ($)"],
  rows: [
    ["17.07.2026", "Bakersfield", "TRK-22", "3.64", "1,123"],
    ["17.07.2026", "Bakersfield", "TBC", "1.45", "TBC"],
    ["17.07.2026", "Fresno", "TRK-09", "5.31", "1,007"],
    ["17.07.2026", "Fresno", "TRK-11", "2.18", "940"],
    ["17.07.2026", "Modesto", "TRK-15", "1.12", "448"],
    ["17.07.2026", "Modesto", "TRK-03", "2.64", "351"],
    ["17.07.2026", "Sacramento", "TRK-03", "0.77", "499"],
    ["", "", "TOTAL", "17.11", "4,368"],
  ],
  truncated: false,
};

export const MOCK_GUARD: GuardReport = {
  pass: true,
  network_calls: 0,
  model_calls: 0,
  checked_at: "2026-07-17T11:05:33-07:00",
  violations: [],
};

export const MOCK_ARTIFACT = `import pandas as pd
import sys

MIN_KG = 500
COLS = ["Date", "Route", "Truck", "Load (t)", "Cost ($)"]

def run(manifest_path, rates_path, out_path):
    m = pd.read_csv(manifest_path)
    r = pd.read_csv(rates_path)
    m = m[m["weight_kg"] >= MIN_KG].copy()
    m = m.merge(r, on="carrier_code", how="left")
    cost = m["base_fee_usd"] + m["rate_per_km_usd"] * m["distance_km"]
    m["Cost ($)"] = cost.round(0)
    m["Load (t)"] = (m["weight_kg"] / 1000).round(2)
    m["Truck"] = m["truck_id"].fillna("TBC")
    m.loc[m["truck_id"].isna(), "Cost ($)"] = None
    m["Date"] = pd.to_datetime(m["date"]).dt.strftime("%d.%m.%Y")
    m["Route"] = m["destination"]
    m = m.sort_values(["Route", "Cost ($)"], ascending=[True, False])
    out = m[COLS].copy()
    total = {"Truck": "TOTAL",
             "Load (t)": out["Load (t)"].sum().round(2),
             "Cost ($)": out["Cost ($)"].sum()}
    out = pd.concat([out, pd.DataFrame([total])], ignore_index=True)
    out["Cost ($)"] = out["Cost ($)"].map(
        lambda v: "TBC" if pd.isna(v) else f"{int(v):,}")
    out.to_csv(out_path, index=False)

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
`;

export function previewToCsv(p: FilePreview): string {
  const esc = (v: string) => (v.includes(",") ? `"${v}"` : v);
  return [p.columns.map(esc).join(","), ...p.rows.map((r) => r.map(esc).join(","))].join("\n") + "\n";
}
