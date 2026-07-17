# 06 — Mock Data (the fixture)

> These files are **real and already generated**, sitting in `mock/`. They are internally
> consistent — `mock/_generate_fixture.py` produced the ground truth by applying the seven
> rules mechanically. If you change one input, re-run the generator; do not hand-edit the
> ground truth.

---

## 1. Why the fixture *is* the product

Andrei's ground truth exists because he made it by hand last Tuesday. Ours exists because a
generator made it. Same thing from the loop's point of view: a target the codegen has never
seen, produced by rules the codegen has to rediscover from a prose brief.

**This fixture is tuned.** The seven rules are chosen so that a competent first attempt from a
good model lands around **40%**, and the loop climbs to 100% in **4–5 attempts, 35–50 seconds**.
That is the correct dramatic length for a demo: long enough to watch, short enough to hold a
room. Each rule is independently discoverable from the diff, which is what makes convergence
fast; and each is invisible from the inputs alone, which is what makes attempt 1 fail honestly.

---

## 2. Input A — `mock/manifest_2026-07-14.csv`

The day's cargo manifest. 13 shipments.

```
shipment_id,date,origin,destination,cargo_type,weight_kg,distance_km,carrier_code
SHP-1041,2026-07-14,Oakland,Fresno,palletised,1240,300,PCF
SHP-1042,2026-07-14,Oakland,Bakersfield,palletised,480,460,VLY      ← under 500, dropped
SHP-1043,2026-07-14,Stockton,Fresno,bulk,2900,210,VLY
SHP-1044,2026-07-14,Oakland,Sacramento,refrigerated,860,130,GRN
SHP-1045,2026-07-14,Fremont,Bakersfield,palletised,3150,440,SRA
SHP-1046,2026-07-14,Stockton,Sacramento,palletised,320,75,DLT       ← under 500, dropped
SHP-1047,2026-07-14,Oakland,Fresno,bulk,4020,305,BAY
SHP-1048,2026-07-14,Fremont,Modesto,palletised,940,145,GRN
SHP-1049,2026-07-14,Oakland,Bakersfield,refrigerated,1780,455,DLT
SHP-1050,2026-07-14,Stockton,Modesto,palletised,150,60,VLY          ← under 500, dropped
SHP-1051,2026-07-14,Fremont,Sacramento,bulk,2260,140,MTN            ← carrier NOT on rate card
SHP-1052,2026-07-14,Oakland,Modesto,palletised,410,150,SRA          ← under 500, dropped
SHP-1053,2026-07-14,Stockton,Fresno,palletised,1595,215,SRA
```

Deliberate traps: `origin` and `cargo_type` exist and are **never used in the output** — the
codegen has to work out that they're noise. Andrei never mentioned them, because to him
they're obviously irrelevant. That gap between what a person says and what a person means is
the entire problem this product solves.

## 3. Input B — `mock/carrier_rates_2026-07.csv`

```
carrier_code,carrier_name,truck_id,base_fee_usd,rate_per_km_usd,currency,valid_from
VLY,Valley Haul Co,TRK-03,240.00,1.85,USD,2026-07-01
PCF,Pacific Freightways,TRK-11,310.00,2.10,USD,2026-07-01
GRN,Grand Line Trucking,TRK-07,180.00,1.40,USD,2026-07-01
SRA,Sierra Cartage,TRK-22,265.00,1.95,USD,2026-07-01
DLT,Delta Road LLC,TRK-15,205.00,1.62,USD,2026-07-01
BAY,Bayline Transport,TRK-09,290.00,2.35,USD,2026-07-01
```

Note `MTN` is absent — that's the `TBC` case, and it's why question 2 in the interview exists.
`carrier_name`, `currency`, `valid_from` are noise. The join is `carrier_code`, and the output
column `Truck` comes from **this** file, not the manifest — so the codegen cannot produce the
output without discovering the join.

## 4. Ground truth — `mock/dispatch_summary_14.07.csv`

The one Andrei made by hand. **The codegen never sees this file.** Only the scorer does.

```
Date,Route,Truck,Load (t),Cost ($)
14.07.2026,Bakersfield,TRK-22,3.15,"1,123"
14.07.2026,Bakersfield,TRK-15,1.78,942
14.07.2026,Fresno,TRK-09,4.02,"1,007"
14.07.2026,Fresno,TRK-11,1.24,940
14.07.2026,Fresno,TRK-22,1.59,684
14.07.2026,Fresno,TRK-03,2.90,628
14.07.2026,Modesto,TRK-07,0.94,383
14.07.2026,Sacramento,TRK-07,0.86,362
14.07.2026,Sacramento,TBC,2.26,TBC
,,TOTAL,18.74,"6,069"
```

**10 rows × 5 columns = 50 cells.** That's the strip: 50 ticks, each ~3px wide + 1px gap = a
198px graphic. Sits perfectly in a 720px content column with room for the score. One wrong
cell is one visible gap. This is why the fixture is this size and not 200 rows.

## 5. The seven hidden rules

Each is a thing Andrei says in half a sentence and which takes real code to satisfy. Each
produces a distinct `Finding` kind when violated — that mapping is what makes the loop
converge instead of thrash.

| # | Rule | Says it as | Finding when wrong | Cells poisoned |
|---|---|---|---|---|
| 1 | Drop `weight_kg < 500` | "skip the little stuff, under half a tonne isn't worth the diesel" | `EXTRA_ROW` ×4 | 20 |
| 2 | `Load (t)` = kg ÷ 1000, 2dp | "loads in tonnes not kilos" | `UNIT` (ratio ≈1000) | 10 |
| 3 | `Cost ($)` = `base_fee + rate_per_km × distance_km`, round to whole dollars | "work out the cost per run" | `ROUNDING` or `VALUE` | 9 |
| 4 | Carrier not on rate card → `Truck` and `Cost` both `TBC` | (answer to question 2) | `VALUE` on 2 cells | 2 |
| 5 | Dates `DD.MM.YYYY` | never says it — **guessed**, settled by the example | `DATE_FORMAT` | 9 |
| 6 | Sort `Route` A→Z, then `Cost` desc; `TBC` last within a route | "my order" | `ROW_ORDER` — **one finding, not 50** | (all, if aligned positionally) |
| 7 | `TOTAL` row: `Load (t)` and `Cost ($)` summed (TBC excluded), other columns empty | "total at the bottom" | `TOTALS_ROW` | 5 |

Plus the format guess: `Cost ($)` uses a comma thousands separator and no cents → `NUMBER_FORMAT`.

**Rule 6 is why the scorer aligns on a key.** A naive positional diff turns one sort bug into
50 wrong cells, the score collapses to 0.1, the repairer gets a wall of noise, and the loop
dies. Key-aligned, the same bug is a single `ROW_ORDER` finding, the repairer fixes it in one
shot, and attempt 4's slip reads *"Sorted the rows the way you asked."* The scorer's alignment
strategy is the difference between a loop that works and a loop that looks like it's working.
Say that to the judges.

## 6. The expected trajectory

Tune the fixture until you get roughly this. If you don't, the problem is the scorer's
findings, not the model.

| # | Score | Strip | Slip headline | What the repairer got |
|---|---|---|---|---|
| 1 | **0.41** | 20/50 | *"Read both files. Guessed at your column names, and I've used kilos."* | `COLUMN_NAME`(w=50) `UNIT`(10) `EXTRA_ROW`(20) `TOTALS_ROW`(5) `DATE_FORMAT`(9) |
| 2 | **0.68** | 34/50 | *"It was writing kilos where you wanted tonnes. Small runs are still in there."* | `EXTRA_ROW`(20) `TOTALS_ROW`(5) `ROW_ORDER` |
| 3 | **0.89** | 43/50 | *"Dropped the small runs and added the total at the bottom. Rows are in the wrong order."* | `ROW_ORDER` `NUMBER_FORMAT`(3) |
| 4 | **0.97** | 47/50 | *"Sorted the rows the way you asked. One cost is a dollar off."* | `ROUNDING`(3) |
| 5 | **1.00** | 50/50 | *"Every cell matches yours."* | — → **STAMP** |

Attempt 1 at 41% is the honest measurement that justifies the entire product's existence: a
good model, given a clear brief from a competent human, gets **less than half** of a routine
office chore right on the first try. Nobody would use that. The loop is what makes it useful.
**That is the pitch.** Say the number.

## 7. The live-demo files

`mock/manifest_2026-07-17.csv` + `mock/carrier_rates_2026-07b.csv` — "today's" files, dropped
onto the trained intern at the end of the demo. 9 shipments, 2 under 500 kg, 1 `MTN` → `TBC`.
Different data, same shape.

Expected output (`mock/_reference_summary_17.07.csv` — **for your verification only, never
shipped**):

```
Date,Route,Truck,Load (t),Cost ($)
17.07.2026,Bakersfield,TRK-22,3.64,"1,123"
17.07.2026,Bakersfield,TBC,1.45,TBC
17.07.2026,Fresno,TRK-09,5.31,"1,007"
17.07.2026,Fresno,TRK-11,2.18,940
17.07.2026,Modesto,TRK-15,1.12,448
17.07.2026,Modesto,TRK-03,2.64,351
17.07.2026,Sacramento,TRK-03,0.77,499
,,TOTAL,17.11,"4,368"
```

**Add an E2E test that runs the trained artifact on the 17th's files and asserts byte-equality
with this.** That test is the proof the loop learned the *rules* and not the *answers* — it's
the anti-cheat from `05-LOOP-ENGINE.md §6.2`, but empirical. If it passes, you can say on
stage: *"and here's it running on data it has never seen."* If it fails, your loop memorised
Tuesday and you have a demo, not a product.

## 8. `mock/brief.json`

The exact text behind the "Use the freight example" button. Deliberately rambling, with a
sentence fragment and a piece of irrelevant colour, because that's how people actually talk:

```json
{
  "brief": "Every morning I get the manifest for the day and the rate card from accounts. I put them together into one summary for the drivers — my columns, my order. Loads in tonnes not kilos because nobody thinks in kilos. Work out the cost per run, that's the base fee plus the per-km rate times how far it's going. Total at the bottom. Skip the little stuff, under half a tonne isn't worth the diesel. Takes me forty minutes and I've been doing it since 2019."
}
```

## 9. `mock/answers.json`

```json
{
  "answers": {
    "q1": "Under 500 kg.",
    "q2": "Keep it, mark the cost as TBC.",
    "q3": "Name it with the date, like the summary I'm giving you."
  }
}
```

## 10. `mock/llm_cassettes/` — do this the moment the loop converges once

Record every `(system, messages) → response` from the successful run. Then:

```bash
LLM_PROVIDER=mock python -m engine.cli train --fixture mock/   # must reproduce §6 exactly
```

If the wifi at AWS Builder Loft dies during your three minutes — and it might — this is the
difference between "we'll take questions" and a demo. **Do not skip this. It is fifteen
minutes of work and it is the cheapest insurance you will buy today.**
