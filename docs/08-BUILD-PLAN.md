# 08 — Build Plan

> It is Friday 17 July 2026. Hacking started at 11:00. **Submission closes at 16:30 and late
> submissions are cut off.** Everything in this file is written backwards from that.

---

## 1. The only thing that matters

At 16:00 you must be able to do this, on one machine, with no explanation:

```
   brief → 3 questions → read-back → drop 3 files → watch 5 slips land → stamp →
   the script → the guard says PASS → drop 2 new files → get a CSV back
```

**Everything else is optional.** Every hour, ask: does this make that path more likely? If no,
cut it. The failure mode of this project is a beautiful landing page and a loop that doesn't
converge at 16:10.

## 2. Task graph

```
  ┌── T0  MAIN THREAD, 11:00–11:35 ─────────────────────────────────────────────┐
  │  Read all docs. Scaffold repo. Write web/lib/types.ts + api/schemas.py.     │
  │  Write web/mocks/events.json (the 5 attempts from 06 §6).                   │
  │  Verify mock/ fixture parses and the generator reproduces the ground truth. │
  │  git init, first commit, public repo, PUSH.  ← do this now, not at 16:25    │
  └───────────────────────────────┬────────────────────────────────────────────┘
                                  │ fan out — 4 subagents, no shared files
     ┌──────────────┬─────────────┴──────────┬─────────────────────┐
     ▼              ▼                        ▼                     ▼
  T1 LOOP        T2 API                   T3 WEB               T4 INFRA
  11:35–14:30    11:35–13:30              11:35–15:00          11:35–13:00
  ─────────      ──────────               ─────────            ──────────
  scorer  ★★★    FastAPI skeleton         tokens + globals.css  Dockerfiles
  + tests        SQLite + 5 tables        components ×11        compose
  runner         upload + sniff           ⑤ training (SSE)  ★   pomerium
  llm(mock)      SSE bus + replay         ④ example            akash SDL
  codegen        job queue                ③ read-back          tool-runtime
  repairer       curl walkthrough §5.9    ① brief
  + anti-cheat                            ② questions
  orchestrator                            ⑥ ready
  cassettes                               /i/[slug]
                                          / landing        ← LAST
     └──────────────┴────────────┬────────────┴─────────────────────┘
                                 ▼
  ┌── T5  MAIN THREAD, 14:30–15:30 ────────────────────────────────────────────┐
  │  Integrate. Live E2E on the fixture. Turn sponsors on ONE AT A TIME,       │
  │  committing after each: Bedrock → Pomerium → Zero → Nexla → Akash.         │
  │  The moment one costs >15 min, flip it to mock, commit, next.              │
  └───────────────────────────────┬───────────────────────────────────────────┘
                                  ▼
  ┌── T6  15:30–16:00  RECORD THE DEMO.  Hard gate. ──────────────────────────┐
  ┌── T7  16:00–16:25  README, Devpost, all teammates attached, PUSH. ────────┘
```

## 3. Timeline with hard gates

| Time | Gate — **if you miss it, cut, don't push** |
|---|---|
| **11:35** | Repo public, `types.ts` written, subagents launched |
| **12:30** | `pytest tests/engine/test_scorer.py` green — a hand-broken script scores ≈0.41 against the fixture. **This is the day's most important gate.** If the scorer is wrong, everything downstream is a lie. |
| **13:00** | INFRA done. `docker compose up` serves web+api. |
| **13:30** | **First real convergence.** `LLM_PROVIDER=bedrock python -m engine.cli train --fixture mock/` reaches ≥0.95. API's curl walkthrough green. |
| **13:35** | **Record the cassettes.** Verify `LLM_PROVIDER=mock` reproduces it. Commit. You now have a demo no matter what happens next. |
| **14:30** | Training screen renders live slips from real SSE. The Ledger animates. |
| **15:00** | WEB done incl. `/i/[slug]` and landing |
| **15:15** | Akash timebox expires — ship the SDL, stop |
| **15:30** | 🔴 **STOP BUILDING. RECORD.** No exceptions. Nothing you add after 15:30 will be worth the risk of not having a video. |
| **16:00** | README + architecture diagram + Devpost draft |
| **16:25** | Submitted. Every teammate on the submission. Repo public — **check in an incognito window.** |

## 4. Cut-list, in the order you cut

Cross these off from the bottom up as time evaporates:

1. Stamp noise filter (`feTurbulence`) — 5 min, pure delight, first to go
2. Landing page below the fold — the hero and the Ledger are enough
3. `/i/[slug]` email address line → grey it, say "next"
4. Nexla → `MOCK_MODE`, keep the narrative
5. Akash → SDL on screen only, no live deploy
6. Zero → one recorded call, shown in the Ledger as "got a new skill"
7. Sandbox layer 7 (docker) → layers 1–6 only
8. `?dev=1` log view
9. The `PLATEAU` / 87% honesty screen → keep the code path, don't polish the UI
10. **Never cut:** the scorer, the Ledger, the read-back, the guard, the cassettes.

## 5. Parallel human work (not for the agents)

- **11:00** — one person registers the whole team on Devpost and AWS Builder **now**. Not at 16:00.
- **11:15** — one person walks the sponsor Discord channels: credits, docs, and *find Nick
  Taylor (Pomerium) and the Nexla judges in person.* A judge who has heard your threat model
  at 11:30 scores you at 16:45 with your framing already in their head. This is worth more
  per minute than any code written today.
- **12:00** — write the Devpost text while the build runs. Steal from `01-PRODUCT.md §4` and
  `07-SPONSORS.md §8`. Don't write it at 16:15.
- **15:00** — the presenter rehearses `07-SPONSORS.md §8` out loud, with a timer, twice.
  Out loud. With a timer. Twice.

## 6. Bail-outs

| It's 14:00 and… | Do this |
|---|---|
| The loop won't converge past 0.7 | Your findings aren't specific enough. Do **not** touch the prompt. Add finding kinds to the scorer (`05 §5.4`) — the model isn't the problem, its input is. |
| Bedrock IAM is a swamp | `LLM_PROVIDER=anthropic`. Say "Bedrock in the SDL, Anthropic direct today." Move on. Nobody deducts for that. |
| Pomerium won't start | `POMERIUM_ENABLED=false`. Show `config.yaml` on screen, tell the threat model. **The threat model was always worth more than the running proxy.** |
| Zero's programmatic path is unclear | Record one CLI call as a video/asciinema, show it as the "got a new skill" beat, be transparent that it's recorded. Honesty scores; a fake doesn't. |
| The web app is behind at 15:00 | Demo the CLI. `python -m engine.cli train --fixture mock/` streaming rising scores into a terminal is *still a better loop demo than 90% of the room.* The Ledger is the delight; the loop is the substance. |
| Everything is on fire at 15:45 | Record whatever works, submit at 16:00, present the architecture. **A submitted 70% beats an unsubmitted 100% by an infinite margin.** |

## 7. README.md — write it at 16:00, from this skeleton

```markdown
# Intern — train an agent the way you'd train a new hire

Andrei, 38, runs dispatch. Every morning he turns two files into one, his way. 40 minutes.
He's asked twice for a script. It's still on the "later" pile.

Intern takes his brief in plain language, asks three questions, reads the job back to him,
and then — this is the part — learns from **one he did himself**. Two inputs, one output.
That's a complete test suite, and he wrote it by accident by doing his job.

## The loop
plan → act → observe → self-correct, against a reward signal the model cannot author.

  spec      brief + 3 answers → read-back → HUMAN APPROVES → frozen job_spec
  implement codegen writes a standalone pandas script (never sees the target)
  test      sandboxed run → cell-level diff vs his file → DETERMINISTIC findings
  iterate   repairer patches the highest-weight finding → repeat → plateau

Attempt 1: 41%. Attempt 5: 100%. Five tries, 41 seconds.
41% is a good model, a clear brief, and less than half the job right —
that's why this needs a loop and not a chat.

## The claim
**The LLM is the trainer, not the worker.** The shipped tool has no model, no network,
no API key. Enforced by `guards/no_llm_at_runtime.py` and shown in the product.
That's why it's $20 once and not a meter.

## Sponsors
- **AWS Bedrock** — trains it, then leaves
- **Zero.xyz** — gives the agent hands when it hits a wall it can't code around
- **Pomerium** — model-written code doesn't get to roam; his files stay his
- **Akash** — a trained intern is 0.1 CPU and ~$0.30/month, and that IS the business model
- **Nexla** — brings the files from where they already live

## Run it
docker compose up   →   http://localhost:3000   →   "Use the freight example"

## Team
…
```

## 8. Commit discipline

- Public repo from 11:35. `git push` every 20 minutes. A "no previous projects" rule means
  your commit history is your alibi — a repo that appears at 16:20 in one commit looks
  exactly like a rule violation, even when it isn't.
- Small messages: `scorer: unit findings`, `web: ledger slip lands`.
- **Never** commit `.env`, credits, or the fixture cassettes if they contain keys.
- Tag `v1-demo` on whatever you recorded. If someone breaks main at 16:10, you check out the tag.
