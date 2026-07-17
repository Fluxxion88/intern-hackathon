# Demo runbook — record at 15:45, submit by 16:25

## 1. Start the stack (wifi-proof: zero network needed)

```bash
cd "<repo root>"
pkill -f "uvicorn api.main:app" ; rm -rf data/jobs data/intern.db
OPENAI_API_KEY= LLM_PROVIDER=mock .venv/bin/python -m uvicorn api.main:app --port 8000 &
cd web && npm run dev &          # if not already running on :3000
```

`LLM_PROVIDER=mock` replays the recorded live run (cassettes in
`mock/llm_cassettes/`) — identical trajectory, zero network. This is a replay of
a real gpt-5.6-terra training run; say so if asked, honesty scores.

## 2. The click path (follow docs/07 §8 narration; times are the 3-min script's)

1. `localhost:3000` — landing; let the hero Ledger loop once.
2. Sign in: Andrei / andrei@example.com.
3. `/train/new` → **Use the freight example** → Send it to your intern.
4. Answer the 3 questions with the top suggestions (500 kg / TBC / date name).
5. Read-back — hover the **I'M GUESSING ON TWO THINGS** block. Approve.
6. Upload `mock/manifest_2026-07-14.csv` + `mock/carrier_rates_2026-07.csv`
   (top zone), `mock/dispatch_summary_14.07.csv` (bottom). **Start practising.**
7. TRAINING — let it play, don't talk over attempt 1.
   Real recorded trajectory: **68% → 96% → 100%, 3 tries** (say these numbers,
   not the script's 41/5 — ours are real).
8. Ready screen — show **What it learned** (the script) and the
   **No AI inside** card (live guard output: network calls 0, model calls 0).
9. `/i/andrei-dispatch` — drop `mock/manifest_2026-07-17.csv` +
   `mock/carrier_rates_2026-07b.csv` **in any order** (order-insensitivity is
   trained in — mention it). Summary back in ~0.3s, byte-identical to the
   hand-checked reference.
10. Terminal, 4 seconds: `.venv/bin/python guards/no_llm_at_runtime.py
    data/jobs/<job_id>/artifact/tool.py` → PASS.

## 3. Sponsor beats (2:40 in the script)

- LLM trainer: "trains it, then leaves — what runs every morning has no model."
- Pomerium: `deploy/pomerium/config.yaml` + README threat model — "the agent
  writes the code; it doesn't decide what the code may reach."
- Akash: `deploy/akash/deploy.sdl` — 0.1 CPU is the pitch.
- Nexla / Zero: adapters in `api/adapters/nexla.py`, `engine/adapters/zero.py`,
  MOCK_MODE, honest "next" framing.

## 4. If anything breaks

- `git checkout v4-order-proof` — the verified demo state.
- CLI fallback (still beats most demos): 
  `OPENAI_API_KEY= LLM_PROVIDER=mock .venv/bin/python -m engine.cli train --fixture mock/`

## 5. Submission checklist (16:25 hard)

- [ ] 3-min video recorded and uploaded
- [ ] Devpost: text from DEVPOST.md, video link, repo link
- [ ] Every teammate attached to the submission
- [ ] Repo public — check in an incognito window: https://github.com/Fluxxion88/intern-hackathon
