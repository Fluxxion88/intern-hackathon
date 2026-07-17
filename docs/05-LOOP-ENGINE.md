# 05 — The Loop Engine

> This is the heart of the product and the thing being judged. `Autonomy` is 20% of the
> score and it is the criterion most teams will fake. Read this file twice.

---

## 1. The thesis

Almost every agent loop in the wild terminates on **"the model said it looks good."** That's
not a loop, it's a monologue with extra steps. A real loop needs a **reward signal the model
cannot author**.

We have one, and the user handed it to us without knowing:

```
   his two input files   ─┐
                          ├──▶  a transform he does by hand every morning
   his one output file   ─┘

   ⇒ f(input_a, input_b) = expected_output   is a total, checkable specification.
```

The loop's job is to **discover f**. The score is a cell-level F1 against his own work. The
model can lie to us about its confidence; it cannot lie about whether cell `[14]["Cost ($)"]`
equals `4,180`.

**Consequence:** every part of this engine is designed to convert a fuzzy human intention
into a diff, and a diff back into a code patch. The LLM is a **search operator over
programs**, and the human's Tuesday is the **fitness function**.

## 2. The loop

```
 ┌───────────────────────────────────────────────────────────────────────────────┐
 │                                                                               │
 │   PLAN ───────────────────────────────────────────────────────────────┐       │
 │   brief + answers → job_spec (frozen, human-approved)                 │       │
 │                                                                       │       │
 │   ┌───────────────────────────────────────────────────────────┐       │       │
 │   │                                                           ▼       │       │
 │   │   ACT                                                                     │
 │   │   codegen(job_spec, findings?, previous_code?) → script.py                 │
 │   │        │                                                                  │
 │   │        ▼                                                                  │
 │   │   runner(script.py, [in_a, in_b]) → produced.csv | traceback              │
 │   │        │                                                                  │
 │   │        ▼                                                                  │
 │   │   OBSERVE                                                                 │
 │   │   scorer(produced.csv, expected.csv) → {score, strip, findings[]}         │
 │   │        │                                                                  │
 │   │        ├── score ≥ 0.99 ────────────────────▶ PERFECT  ─┐                 │
 │   │        ├── no gain ×2 ───────────────────────▶ PLATEAU ─┤                 │
 │   │        ├── n ≥ 6 or 180s ────────────────────▶ BUDGET  ─┼──▶ FREEZE       │
 │   │        └── otherwise                                    │    best artifact│
 │   │             │                                           │                 │
 │   │             ▼                                                             │
 │   │   SELF-CORRECT                                                            │
 │   │   repairer(findings, code, spec) → patch + headline                       │
 │   │             │                                                             │
 │   └─────────────┘                                                             │
 │                                                                               │
 └───────────────────────────────────────────────────────────────────────────────┘
```

**Never discard the best.** Attempt 5 can be worse than attempt 4. We keep the highest-scoring
artifact and ship that one. The Ledger shows the true sequence (including regressions — that's
honest and it's more convincing than a monotone climb), but the `match` stat and the shipped
tool are always the best-so-far.

## 3. `engine/llm.py`

```python
# Three providers, one interface. mock is not a stub — it replays recorded
# responses from mock/llm_cassettes/*.json so the whole loop can be developed
# and demoed with zero network. Build this SECOND, right after types.
class LLM(Protocol):
    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str: ...

# bedrock   → boto3 bedrock-runtime, converse API   (sponsor: AWS)
# anthropic → direct API                            (fallback)
# mock      → cassette replay, keyed by a hash of (system + messages)
```

**Record cassettes for the freight fixture the moment the loop works once.** That recording is
your demo's life insurance. `LLM_PROVIDER=mock` must produce the full 5-attempt convergence
with no network at all. If the venue wifi dies during your demo — and at hackathons it does —
you flip one env var and nobody knows.

## 4. `engine/planner.py` — PLAN

Three calls, in order. Small, cheap, each with a single job.

### 4.1 Extract

```
SYSTEM
You read a description of a repetitive office file chore, written by someone who is
good at their job and has never written software. Your task is to extract every rule
that constrains the output, and every place the description is ambiguous.

Return JSON only:
{
  "rules":      [{"text": "<one rule, in the writer's own vocabulary>",
                  "confidence": 0.0-1.0,
                  "source": "said" | "inferred"}],
  "ambiguities":[{"question": "<what you'd ask a colleague, one sentence>",
                  "why": "<what breaks if you guess wrong, one sentence>",
                  "cost": 0.0-1.0,
                  "suggestions": ["<likely answer>", "<other likely answer>"]}],
  "noun":       "<one word naming this job, for the URL: 'dispatch'>"
}

Rules:
- Use HIS words. He said "little stuff" — your rule says "little stuff", not
  "records below the weight threshold". You are taking notes, not writing a ticket.
- "cost" is how much a wrong guess would poison training. A wrong unit poisons every
  row: 0.9. An unknown date format shows up in one column and the example will
  settle it: 0.2.
- Never ask something the example files will answer. Date format, column names,
  separators, rounding — the example settles all of these. Ask only about rules that
  are INVISIBLE in the example: thresholds, exception handling, business logic.
```

### 4.2 Rank and cut — **plain Python, no model**

Sort `ambiguities` by `cost` desc, `take(3)`. Everything cut becomes a **guess** that must be
surfaced in the read-back's honesty block. Cheap, deterministic, and it enforces the
three-question cap from `03-SCREENS.md §3` without trusting the model to count.

### 4.3 Compose `job_spec`

After answers come back:

```json
{
  "slug": "andrei-dispatch",
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
    {"n": 7, "text": "Name the columns your way: Date, Route, Truck, Load (t), Cost ($).", "confidence": 0.7, "source": "inferred"},
    {"n": 8, "text": "Put a TOTAL row at the bottom with the load and the cost added up, and nothing in the other columns.", "confidence": 0.9, "source": "said"}
  ],
  "guesses": [
    "Dates like 17.07.2026, because that's how your files are written.",
    "A comma in the thousands, no cents."
  ],
  "output_columns": ["Date", "Route", "Truck", "Load (t)", "Cost ($)"]
}
```

**Once Andrei presses "That's the job", this object is frozen.** The repairer may not edit it.
If the loop plateaus because the *spec* is wrong (not the code), the outcome is `PLATEAU` and
we send him back to the read-back with the specific rule the diff implicates. **The model
never silently rewrites what the human approved.** This is the single most important
constraint in the engine and it's what makes the read-back mean anything.

## 5. `engine/scorer.py` — OBSERVE  ★ the most valuable file in the repo

Everything else is a wrapper around this. Get it right first.

### 5.1 Align, then compare

```python
def score(produced: pd.DataFrame, expected: pd.DataFrame) -> ScoreResult:
    # 1. COLUMNS — set comparison first. Wrong/missing columns are a structural
    #    finding, not a thousand cell errors. Report them once, loudly.
    # 2. ROWS — align on a key if one exists (a column with unique values present
    #    in both), else align positionally. A key-based alignment means a sort-order
    #    bug produces ONE finding ("rows are in a different order") instead of
    #    poisoning every cell — which is what makes attempt 4's message readable.
    # 3. CELLS — compare with a typed comparator, not string equality:
    #      numeric  → abs diff ≤ 0.005 after stripping ',' '$' ' '
    #      date     → parse both, compare the date, and RECORD the format mismatch
    #                 separately (it's a format finding, not a value finding)
    #      string   → exact after strip(); casefold match = a separate finding
    #      empty    → '' == NaN == None
    # 4. Every mismatch → a Finding, not a bool.
```

### 5.2 The number

```
  cell_score      = cells_ok / cells_expected          # the honest headline number
  column_penalty  = 0.5 if column SET differs else 1.0 # structure dominates everything
  row_penalty     = min(rows_produced, rows_expected) / max(...)
  score           = cell_score × column_penalty × row_penalty
```

The column penalty being brutal is deliberate: getting 48 cells right under the wrong headings
is not 90% of the job, it's a different file. Andrei can't use it.

### 5.3 The strip

```python
  strip = "".join("1" if ok else "0" for ok in cells_row_major)
```

One char per expected cell, row-major. This drives `<CellStrip>` — the thing Andrei actually
watches. **~50 cells is the sweet spot for the fixture:** enough to fill a strip legibly,
few enough that one wrong cell is visible as one gap. The fixture in `06-MOCK-DATA.md` lands on
exactly 50 (10 rows × 5 columns).

### 5.4 Findings — **the whole game is here**

A finding must be **specific enough to patch from.** "Output doesn't match" is worthless.
This is the difference between a loop that converges in 5 attempts and one that thrashes for
20 and never gets there.

```python
@dataclass
class Finding:
    kind: str        # MISSING_COLUMN | EXTRA_COLUMN | COLUMN_NAME | ROW_COUNT | ROW_ORDER
                     # | UNIT | ROUNDING | DATE_FORMAT | NUMBER_FORMAT | VALUE | MISSING_ROW
                     # | EXTRA_ROW | TOTALS_ROW | CRASH
    column: str | None
    examples: list[tuple[str, str, str]]   # (row_key, produced, expected) — MAX 3
    hint: str        # a hypothesis, for the repairer's eyes only
    weight: float    # how many cells this explains — the repairer fixes the biggest first
```

**Findings are inferred by rules, not by the model.** This is a deliberate architecture
choice and you should say it out loud to the judges:

| Rule | Emits |
|---|---|
| expected/produced ratio ≈ 1000 across a numeric column | `UNIT` — "kilos vs tonnes, factor of 1000" |
| every value differs by <1 and rounds equal | `ROUNDING` |
| same values, different positions, key alignment succeeds | `ROW_ORDER` |
| both parse as dates, strings differ | `DATE_FORMAT` — "produced 2026-07-17, expected 17.07.2026" |
| numeric equal, string differs, `,` present in one | `NUMBER_FORMAT` |
| expected has a row where the key col is empty and numeric cols = column sums | `TOTALS_ROW` |
| produced rows ⊂ expected rows | `MISSING_ROW` + the dropped rows' distinguishing feature |
| column sets differ after casefold/strip | `COLUMN_NAME` (vs `MISSING_COLUMN`) |

Deterministic finding extraction is *why the loop is fast*. A model staring at two CSVs
guesses. A model handed `UNIT: Load (t), produced 2900 expected 2.90, factor 1000.0` patches
in one shot. **We do the observing with code and spend the model only on the correcting.**

That sentence is your answer to "what makes your loop different." Have it ready.

### 5.5 Crash is a finding

Traceback → `Finding(kind=CRASH, hint=<last 15 lines>)`, score 0.0, loop continues. A crash on
attempt 1 is *expected* and it's fine — attempt 1 crashing and attempt 2 scoring 0.68 is a
better demo than attempt 1 scoring 0.41, because it shows the loop *recovering*. Don't
engineer the crash away.

## 6. `engine/repairer.py` — SELF-CORRECT

### 6.1 Prompt

```
SYSTEM
You are fixing a Python script so its output matches a target file exactly.

You get: the frozen spec (approved by the user — TREAT AS LAW), the current script,
and a list of findings from a deterministic diff. The findings are FACTS, not
opinions. Do not re-derive them. Do not question them.

Return JSON only:
{
  "code":     "<the complete corrected script>",
  "changed":  "<what you changed, ≤6 words, e.g. 'rounding on the Cost column'>",
  "headline": "<what a non-technical person would understand, ≤14 words, plain
               English, no jargon: 'Sorted the rows the way you asked. One cost
               is a dollar off.'>"
}

Rules:
1. Fix the HIGHEST-WEIGHT finding first. One structural fix beats five cosmetic ones.
2. Never fix a finding by hard-coding expected values. If you write a literal from
   the target file into the script, you have cheated and the tool is worthless on
   tomorrow's data. This is the only unforgivable error.
3. Never add a dependency. pandas and the stdlib. Nothing else.
4. Never make a network call, import requests/urllib/socket/httpx, or call a model.
5. If a finding contradicts the spec, DO NOT change the code — set
   "code": null and explain in "headline". The human's spec wins over your reading
   of the diff, and a human will be told.
6. The headline is read by a dispatch manager, not an engineer. "Fixed the unit
   conversion" — no. "It was writing kilos where you wanted tonnes" — yes.
```

### 6.2 Anti-cheat — **enforce in code, not in the prompt**

Rule 2 is the one a model will break under pressure, and if it does, the entire product is a
fraud. Check it:

```python
def rejects_hardcoding(code: str, expected: pd.DataFrame) -> str | None:
    # every distinctive literal from the target that appears verbatim in the source
    # is a red flag. Route names, ids, and cost values in particular.
    literals = distinctive_values(expected)     # len>3, not in inputs, not common words
    hits = [v for v in literals if repr(v) in code or f'"{v}"' in code]
    if len(hits) >= 2:
        return f"hardcoded target values: {hits[:3]}"
    return None
```

On a hit: discard the attempt, re-prompt once with the violation quoted back, and if it does
it again, stop and report `FAILED`. **Then say this on stage.** "We check that the model
didn't cheat by memorising the answer" is a sentence that makes an experienced judge sit up,
because they've all seen a demo that was secretly doing exactly that.

### 6.3 The headline is a product surface

The `headline` field lands directly on a `<LedgerSlip>` in front of Andrei. It is not a log
line. Bad → good:

| ✗ | ✓ |
|---|---|
| `Applied unit conversion to weight column` | `It was writing kilos where you wanted tonnes.` |
| `Sort order corrected per spec rule 6` | `Sorted the rows the way you asked.` |
| `AssertionError: 1 cell mismatch at [14]` | `One cost is a dollar off.` |
| `Added aggregate row` | `Added the total at the bottom.` |
| `Initial implementation` | `Read both files. Guessed at your column names.` |

## 7. `engine/orchestrator.py` — termination

```python
PERFECT  = score >= 0.99
PLATEAU  = best hasn't improved by >= 0.02 for 2 consecutive attempts   (and n >= 3)
BUDGET   = n >= MAX_ATTEMPTS (6)  or  elapsed >= 180s
FAILED   = terminal and best < 0.4,  or  anti-cheat tripped twice,  or  spec contradiction
```

On any terminal state: freeze `best_artifact`, run the guard, emit `converged`, write
`artifact/`.

**Tuning for the demo:** the fixture in `06-MOCK-DATA.md` is designed to land on `PERFECT` at
attempt 4–5, in 35–50 seconds. That is the right length: long enough that people watch slips
land and *feel* the loop, short enough that you don't lose the room. If it converges at
attempt 2, your fixture is too easy — add a rule. If it takes 8, your findings aren't specific
enough — fix the scorer, not the prompt.

## 8. `engine/codegen.py` — the first attempt

```
SYSTEM
Write a standalone Python script implementing the spec below.

Signature:  python tool.py <input_a.csv> <input_b.csv> <output.csv>
Allowed:    pandas, and the Python standard library. Nothing else.
Forbidden:  network of any kind, subprocess, eval/exec, reading any file that isn't
            argv[1] or argv[2], writing any file that isn't argv[3], any AI/model call.
Style:      one `run()` function, constants at the top with the same names the user
            used, a comment above each block quoting the spec rule number it
            implements. This script is shown to the person who wrote the spec — the
            comments are for them.

You do NOT get to see the target file. Implement the spec, not the answer.

Return JSON only: {"code": "<script>", "headline": "<≤14 words, plain English,
what you did and what you had to guess>"}
```

**`codegen` is deliberately blind to the expected output.** Only the *scorer* sees it, and
only *findings* leak back. This preserves the loop's integrity: attempt 1 is an honest
attempt at the spec, so its ~40% score is a real measurement of how underspecified natural
language is — which is the entire premise of the product. Give the model the target and you've
built a very expensive `cp`.

Comments citing rule numbers matter: on the `ready` screen Andrei reads
`# rule 5: turn kilos into tonnes, 2dp` next to the line that does it. His spec and his
program are the same document. That's the read-back paying off twice.

## 9. `guards/no_llm_at_runtime.py` — the claim, enforced

```python
BANNED_IMPORTS = {"anthropic","openai","boto3","requests","httpx","urllib","socket",
                  "aiohttp","subprocess","openai_agents","langchain","litellm"}
BANNED_CALLS   = {"eval","exec","compile","__import__","system","popen"}

def check(path) -> dict:
    tree = ast.parse(Path(path).read_text())
    # walk Import/ImportFrom → banned imports
    # walk Call → banned builtins
    # regex the source for r"https?://" and r"sk-[A-Za-z0-9]{20,}"
    return {"pass": bool, "network_calls": int, "model_calls": int,
            "checked_at": iso, "violations": [...]}
```

Runs on every attempt (a violating attempt is discarded before it can even be scored) and once
more on the frozen artifact. Its JSON output renders the "No AI inside" card on
`/train/[id]/ready`. **Run it live on stage.** A green PASS on a script the audience just
watched a model write is the most persuasive 4 seconds in your 3 minutes.

## 10. Sequence

```
 Andrei          web            api          planner     codegen    runner    scorer   repairer
   │              │              │              │           │         │         │         │
   ├─ brief ─────▶│──POST /jobs─▶│──extract────▶│           │         │         │         │
   │              │              │◀─rules,ambig─┤           │         │         │         │
   │◀─ 3 questions┤◀─────────────┤ rank+cut(3)  │           │         │         │         │
   ├─ answers ───▶│──/answers───▶│──compose────▶│           │         │         │         │
   │◀─ read-back ─┤◀─ job_spec ──┤              │           │         │         │         │
   ├─ approve ───▶│              │  FREEZE SPEC │           │         │         │         │
   ├─ 3 files ───▶│──/files─────▶│  sniff+preview                     │         │         │
   ├─ train ─────▶│──/train─────▶│                                    │         │         │
   │              │◀═ phase:WRITING ═════════════════════════════════════════════════════ │
   │              │              │──spec───────────────────▶│         │         │         │
   │              │              │◀─script.py───────────────┤         │         │         │
   │              │◀═ phase:RUNNING ═╡                                │         │         │
   │              │              │──script+inputs────────────────────▶│         │         │
   │              │              │◀─produced.csv─────────────────────┤         │         │
   │              │◀═ phase:CHECKING ═╡                                          │         │
   │              │              │──produced+expected──────────────────────────▶│         │
   │              │              │◀─score .41, strip, findings[]────────────────┤         │
   │◀═ SLIP 1 lands ═════════════╡                                              │         │
   │              │◀═ phase:FIXING ═╡                                                     │
   │              │              │──findings+code+spec────────────────────────────────────▶│
   │              │              │◀─patch, headline───────────────────────────────────────┤│
   │              │              │  anti-cheat check                                       │
   │              │              │  ⟳ ×4                                                   │
   │◀═ SLIP 5, score 1.0 ════════╡                                                         │
   │◀═ converged ════════════════╡  freeze artifact, run guard, write artifact/            │
   │◀─ STAMP ─────┤              │                                                         │
```

## 11. What to build first (LOOP subagent's order — do not deviate)

1. `scorer.py` + its unit tests against `mock/`. **Half your value is here.** You can
   hand-write a deliberately-broken `tool.py` and assert it scores 0.41. Do that before any
   model is involved.
2. `runner.py` with layers 1–6.
3. `llm.py` with `mock` provider only.
4. `codegen.py` → first real attempt, live against Bedrock.
5. `repairer.py` + anti-cheat.
6. `orchestrator.py` + events.
7. Record cassettes. Verify `LLM_PROVIDER=mock` converges identically.
8. `cli.py` so the whole thing runs without the web app existing.

If you build the orchestrator first you will spend three hours debugging a loop whose scorer
lies to it. The scorer is the ground; build the ground first.
