# 01 — Product

## 1. The person

**Andrei, 38.** Dispatch manager at a mid-size freight company. Fifteen years in logistics.
Excellent at his job. Uses Excel, Outlook, and a carrier portal. He has never opened a
terminal and has no intention of starting.

Every morning he opens two files — the day's cargo manifest and the current carrier rate
card — and rebuilds them into one summary in *his* format, because his format is the one
his drivers and his boss understand. It takes 40 minutes. It has taken 40 minutes for six
years. That's 160 hours a year of a senior person doing arithmetic.

He knows a script could do this. He has asked twice. Both times it died in the gap between
"explain the task to a developer" and "the developer has time." So it stays on the *later*
pile, forever.

### What he is NOT

- He is not going to install Claude Code.
- He is not going to reason about API keys, models, or context windows.
- He is not going to trust a black box that says "Done!" — he will trust something that
  shows him it produced *his* file from *his* files.
- He is not price-sensitive at $20. He is **hassle-sensitive**. A per-token meter is a
  reason to not start. A subscription is a thing to cancel. One payment, one tool, done.

## 2. The insight the product is built on

> Andrei cannot write a spec. But he already **has** one, and he doesn't know it:
> **two input files and the one output file he made from them last Tuesday.**

That worked example is a complete, machine-checkable specification of his intent. It is the
test suite. He produced it by hand and it took him 40 minutes, and it is worth more than any
requirements document he could dictate.

This is the whole trick. **The user's habit is the eval.**

## 3. The metaphor: train an intern

The interface never says *agent*, *model*, *prompt*, *deploy*, *pipeline*, or *AI*. It uses
the words of the thing Andrei has done a hundred times — showing a new hire how the job is
done.

| System concept | What we call it | Why |
|---|---|---|
| Task description prompt | **The brief** | He gives briefs to people already. |
| Model restates the spec | **Read-back** | Radio/dispatch discipline: you read the order back. |
| Uploading the worked example | **Show me one you did** | The single most natural instruction in any handover. |
| Agent loop iterations | **Training** / **attempts** | An intern gets it wrong, you correct them, they improve. |
| Score vs expected output | **Match** (a %) | Honest, and he can decide if 94% is good enough. |
| Deployment | **First day** | The intern starts working. |
| The produced script | **What it learned** | Downloadable. His property. |

The read-back is not decoration. It is the trust mechanism: <cite>agentic interfaces should
disclose capability and communicate uncertainty proactively rather than letting the user
discover errors</cite>. Andrei approves a plan written in his own vocabulary before a single
line of code exists.

## 4. The demo story (this exact story, nothing else)

```
  1. Andrei opens intern.works. One field. One sentence of instruction.
  2. He types, in his words, roughly:
       "Every morning I get a cargo manifest and a rate card. I merge them into
        one summary for my drivers — my columns, my order, tonnes not kilos,
        with the cost worked out and a total at the bottom. Small loads I skip."
  3. Intern asks three questions. Not thirty. Three.
       - "What counts as a small load?"
       - "If a carrier isn't on the rate card, drop the row or flag it?"
       - "Should the file be dated, and in what format?"
  4. Intern reads the job back in plain English, as a numbered list of rules.
       Andrei fixes one line ("no, sort by destination first"). Approves.
  5. "Show me one you did." He drags in manifest.csv, rates.csv, and the
      summary.csv he built by hand last Tuesday.
  6. TRAINING. The Ledger fills, live:
       Attempt 1 ····· 41% match   "columns named wrong, kilos not tonnes"
       Attempt 2 ····· 68% match   "unit fixed; totals row missing"
       Attempt 3 ····· 89% match   "totals added; sort order wrong"
       Attempt 4 ····· 97% match   "sorted; 1 rounding cell off"
       Attempt 5 ····· 100% match  ✓ STAMPED
  7. "Your intern is ready." A URL. He drops today's two files on it.
      Gets his summary. It took 1.2 seconds and cost us $0.0004.
  8. Reveal for the judges: open the produced script. It's 60 lines of pandas.
      No API key. No model. No network. `guards/no_llm_at_runtime.py` PASS.
      That's why $20 flat works.
```

## 5. Why this is loop engineering and not a chatbot

The hackathon asks for agents that **plan, act, observe, and self-correct across the full
build cycle, from spec to implementation to testing and iteration.** Map it:

| Hackathon phase | Our loop |
|---|---|
| **Spec** | Interview → read-back → user approval. The spec is negotiated, then frozen as `job_spec.json`. |
| **Implementation** | `codegen` writes a standalone Python script from the frozen spec. |
| **Testing** | `runner` executes it in a sandbox on the real inputs; `scorer` diffs the output against the user's own worked example, cell by cell. |
| **Iteration** | `repairer` receives a structured diff — not a vibe — and patches. Repeat until plateau. |

The critical difference from 90% of what will be on stage today: **we have an objective
function.** Most demos will loop until the model says "looks good." We loop until a
cell-level F1 against a human-authored ground truth stops improving. The reward signal is
the user's own Tuesday.

## 6. Convergence and honesty

The loop stops on one of four conditions (see `05-LOOP-ENGINE.md §7`):

- `PERFECT` — score ≥ 0.99
- `PLATEAU` — no improvement ≥ 0.02 for 2 consecutive attempts
- `BUDGET` — attempt cap (default 6) or wall-clock cap (default 180s) hit
- `FAILED` — score < 0.4 at cap

If we plateau at 0.87 we say so, in his language:

> **"Your intern gets 87% of this right on its own. The 3 rows it can't do are marked in
> the file for you to finish. That's still 35 of your 40 minutes back."**

Never claim 100%. A tool that is honestly 87% is adopted; a tool that claims 100% and is
87% is uninstalled. This is a first-class product feature and it is *on the screen*.

## 7. Business model (one slide, don't build it)

- **$20 once, per intern.** Not per seat, not per run, not per token.
- Possible because the trained artifact has **no marginal model cost**. Post-training,
  a run is a container spinning for ~1s. Hosting a produced tool ≈ $0.30/month on Akash.
- Training cost: ~$0.40 of Bedrock tokens, once. Gross margin ≈ 97%.
- We charge for **not having to think about it**: hosting, the URL, the fact that it keeps
  working when Andrei's laptop is replaced.
- This is the answer to "why won't OpenAI eat you": we're not selling intelligence,
  we're selling the removal of every decision between a person and a working tool.

## 8. Scope fence — v0 (today)

**IN**
- One vertical: two CSV inputs → one CSV output, deterministic transform
- Interview (3 questions max) → read-back → approve
- Worked-example upload (2 in, 1 expected out)
- Training loop with live Ledger and cell-level scoring
- Produced tool deployed behind a URL with a drop-zone
- Download the produced script
- Mocked session (a cookie with a name; no password)

**OUT** — say these are "next" if a judge asks; do not build
- PDF/xlsx/email ingestion (the Zero adapter is *wired* and demoed on one call, not the path)
- Payments, accounts, teams
- Editing a trained intern after the fact (only retrain)
- More than one worked example (the design supports N; we ship 1)

## 9. Naming

- Product: **Intern**
- The trained artifact: **an intern** (lowercase). "Andrei's dispatch intern."
- Verb: **train**, never *build* or *generate*.
- The company/venue: **Intern Studio** only in code namespaces, never in UI.
