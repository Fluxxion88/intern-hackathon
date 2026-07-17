# Devpost draft — paste into the submission form

## Project name

Intern — train an agent the way you'd train a new hire

## Elevator pitch (200 chars)

Describe a file chore in plain words, show one example you did by hand, and an
LLM loop trains a deterministic tool that does it forever. No AI at runtime. $20
once.

## Inspiration

Andrei, 38, runs dispatch at a freight company. Every morning he merges the
day's manifest and the rate card into one summary, his way. Forty minutes, six
years. He's asked for a script twice; it died in the gap between "explain it to
a developer" and "the developer has time." He will never install a CLI or think
about API keys. But he already owns a perfect spec and doesn't know it: two
input files and the output he built from them last Tuesday.

## What it does

Intern interviews you in plain language (three questions, never more), reads the
job back as numbered rules in your own words — including what it's guessing —
and then trains against one worked example you upload. The loop writes a Python
script, runs it sandboxed, diffs the output against your file cell by cell, and
repairs the biggest problem first. When it converges, the model is removed. You
get a URL: drop today's files, get your summary in about a second, forever.

## The loop (this is the hackathon's brief, literally)

- **Spec**: brief + 3 answers → read-back → human approves → frozen job_spec.
  The repairer may never edit what the human approved.
- **Implement**: codegen writes a standalone pandas script. It never sees the
  target file.
- **Test**: sandboxed run (subprocess, empty env, rlimits, AST static check) →
  cell-level diff against the user's own example.
- **Iterate**: the diff becomes typed, weighted findings (UNIT, ROW_ORDER,
  TOTALS_ROW, DATE_FORMAT…) inferred by rules, not by the model. The repairer
  fixes the heaviest first.

We observe with code and spend the model only on correcting. That's why the
loop converges in 3–5 attempts instead of thrashing: a model staring at two
CSVs guesses; a model handed "UNIT: factor 1000, produced 2900, expected 2.90"
patches in one shot.

**The reward signal cannot be authored by the model.** Most agent demos loop
until the model says "looks good." Ours loops until a cell-level F1 against a
human-authored ground truth stops improving.

Recorded run: attempt 1 **68%**, attempt 2 **96%**, attempt 3 **100%**, 53
seconds. Then we run the trained tool on the NEXT day's files — data it has
never seen — and the output is byte-identical to the hand-checked reference.
An anti-cheat check rejects any attempt that hard-codes values from the target,
so the loop provably learned the rules, not the answers. Drop the two files in
either order; it works — the script identifies each file by its headers.

## The claim that makes it a business

**The LLM is the trainer, not the worker.** The shipped tool has no model, no
network, no API key — enforced by `guards/no_llm_at_runtime.py` (AST walk, run
on every attempt and on the final artifact) and rendered in the product as the
"No AI inside" card, from the guard's real output. Training costs cents, once;
a run is a 0.3-second subprocess. That's why it's $20 once and not a meter.

## Sponsors

- **Pomerium** — we execute model-written code, on files a stranger uploaded,
  for someone who can't read the code. Identity-aware proxy in front (per-intern
  route policies — his drivers see his intern, nobody else's), and the sandbox
  egress story behind: the agent writes the code; it doesn't decide what the
  code may reach. `deploy/pomerium/config.yaml`.
- **Akash** — a trained intern is 0.1 CPU / 128Mi (`deploy/akash/deploy.sdl`)
  because there's no model inside. We're not using Akash for GPUs; we're using
  it because a trained intern is a rounding error and should be priced like one.
  That IS the unit economics of $20-once.
- **Nexla** — the last mile: files arrive from where they already live. One
  trained intern = one Nexla flow (inbox source → our artifact → his folder).
  Adapter wired with MOCK_MODE; live path marked TODO with their judges.
- **Zero.xyz** — when training hits a capability wall (a scanned PDF instead of
  a CSV), the trainer discovers a service and bakes the learned step into the
  deterministic artifact. Zero unblocks the agent; we unblock the human.
  Neither of us asks anyone for an API key.
- **LLM trainer** — provider-agnostic adapter (openai / bedrock / anthropic /
  mock). The demo replays a recorded real training run with zero network.

## How we built it

Two services: Next.js 15 (Tailwind v4, no component libraries, a monochrome
"Carbon Copy" design system — paper, ink, hairlines, one rubber stamp) and
FastAPI + SQLite + SSE. The engine is a plain Python library: scorer first
(half the value is there), then sandbox runner, codegen, repairer, orchestrator.
29 tests including: a hand-broken script must score ≈0.41, and the trained
artifact must reproduce the unseen day byte-for-byte.

## What's next

PDF/xlsx ingestion via Zero, the email path via Nexla, one Akash deployment per
intern, more than one worked example.

## Try it

```
docker compose -f deploy/docker-compose.yml up  →  localhost:3000  →  "Use the freight example"
```

Repo: https://github.com/Fluxxion88/intern-hackathon
