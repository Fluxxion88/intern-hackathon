# Intern — train an agent the way you'd train a new hire

Andrei, 38, runs dispatch. Every morning he turns two files into one, his way. 40 minutes.
He's asked twice for a script. It's still on the "later" pile.

Intern takes his brief in plain language, asks three questions, reads the job back to him,
and then — this is the part — learns from **one he did himself**. Two inputs, one output.
That's a complete test suite, and he wrote it by accident by doing his job.

## The loop

plan → act → observe → self-correct, against a reward signal the model cannot author.

```
  spec       brief + 3 answers → read-back → HUMAN APPROVES → frozen job_spec
  implement  codegen writes a standalone pandas script (never sees the target)
  test       sandboxed run → cell-level diff vs his file → DETERMINISTIC findings
  iterate    repairer patches the highest-weight finding → repeat → plateau
```

Our recorded run: attempt 1 **68%**, attempt 2 **96%**, attempt 3 **100%** — 53 seconds.
A good model, a clear brief, and a third of the job still wrong on the first try —
that's why this needs a loop and not a chat. The Ledger shows the true sequence,
including the runs where attempt 1 crashed outright; the loop recovers, keeps the
best artifact, and never claims a score it didn't measure.

## The claim

**The LLM is the trainer, not the worker.** The shipped tool has no model, no network,
no API key. Enforced by `guards/no_llm_at_runtime.py` and shown in the product.
That's why it's $20 once and not a meter.

## Architecture

```
   Andrei's browser ──▶ POMERIUM :443 (identity-aware proxy, per-intern route policies)
                          │                  │
                 /*       ▼         /api/*   ▼
              WEB :3000 (Next.js 15) ──SSE──▶ API :8000 (FastAPI)
                                              ├── engine/   the training loop
                                              ├── store/    SQLite
                                              ├── sandbox/  subprocess, env={}, rlimits, AST check
                                              └── adapters/ sponsors, every one with MOCK_MODE
                                              │
              trainer only ──▶ LLM (trains it, then leaves — runtime is AI-free)
              artifact     ──▶ tool-runtime container → Akash (0.1 CPU, ~$0.30/month)
              file delivery ──▶ Nexla (inbox → intern → back to where his files live)
```

The scorer observes with code, not vibes: a cell-level diff against the user's own worked
example produces typed findings (`UNIT`, `ROW_ORDER`, `TOTALS_ROW`…) weighted by how many
cells they explain. The model only ever corrects; it never gets to grade itself. An
anti-cheat check rejects any attempt that hard-codes values from the target file, and an
E2E test runs the trained artifact on data it has never seen.

## Sponsors

- **Zero.xyz** — gives the agent hands when it hits a wall it can't code around; used at
  training time, the learned step is baked into the deterministic artifact
- **Pomerium** — model-written code doesn't get to roam; his files stay his. Identity in
  front, egress policy behind
- **Akash** — a trained intern is 0.1 CPU and ~$0.30/month, and that IS the business model
- **Nexla** — brings the files from where they already live
- LLM trainer via the provider adapter (`engine/llm.py`): openai / bedrock / anthropic /
  mock (cassette replay — the demo runs with zero network)

## Run it

```
docker compose -f deploy/docker-compose.yml up   →   http://localhost:3000
```

then press **"Use the freight example"**.

Dev mode: `.venv/bin/python -m uvicorn api.main:app --port 8000` + `cd web && npm run dev`.
CLI-only loop demo: `LLM_PROVIDER=mock .venv/bin/python -m engine.cli train --fixture mock/`

## Team

Dynamic Resonance — team@dynamicresonance.ai
