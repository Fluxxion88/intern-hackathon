# 04 — Architecture

## 1. Shape

Two services and a runtime image. Nothing else. Every additional moving part is a way to
lose at 16:20.

```
                          ┌─────────────────────────────────────────┐
   Andrei's browser ─────▶│  POMERIUM  :443                         │  identity-aware proxy
                          │  - fronts everything                    │  (sponsor: Pomerium)
                          │  - injects X-Intern-User                │
                          │  - policy per route                     │
                          └───────┬─────────────────────┬───────────┘
                                  │                     │
                       /*         │                     │  /i/*, /api/*
                                  ▼                     ▼
                    ┌──────────────────────┐   ┌──────────────────────────────┐
                    │  WEB  :3000          │   │  API  :8000                  │
                    │  Next.js 15          │──▶│  FastAPI + uvicorn           │
                    │  App Router, RSC     │SSE│  ├── engine/   (the loop)    │
                    │  Tailwind v4         │◀──│  ├── store/    (SQLite)      │
                    │  no component lib    │   │  ├── sandbox/  (subprocess)  │
                    └──────────────────────┘   │  └── adapters/ (sponsors)    │
                                               └───────┬──────────────────────┘
                                                       │
                            ┌──────────────────────────┼──────────────────────────┐
                            ▼                          ▼                          ▼
                  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
                  │  AWS Bedrock     │      │  Zero.xyz        │      │  Akash           │
                  │  Claude Sonnet   │      │  capability      │      │  tool-runtime    │
                  │  (trainer only)  │      │  broker          │      │  container/tool  │
                  └──────────────────┘      └──────────────────┘      └──────────────────┘
                            ▲                          ▲                          ▲
                            └──────────── all behind adapters with MOCK_MODE ─────┘

                  ┌──────────────────────────────────────────────────────────┐
                  │  NEXLA — data delivery: inbox/drive → job, job → dest    │
                  │  demoed on the /i/[slug] email path                      │
                  └──────────────────────────────────────────────────────────┘
```

**Why FastAPI and not "all Next.js":** the produced artifact is Python, the runner executes
Python, the scorer is pandas. Putting the loop in the same language as the thing it writes
removes an entire class of bugs and lets the engine be a plain importable library that the
LOOP subagent can develop and test with zero web stack in the way.

## 2. Repo layout

```
intern/
├── docs/                         ← this spec. read-only during the build.
├── web/                          ← AGENT: WEB owns this
│   ├── app/
│   │   ├── page.tsx                        /
│   │   ├── start/page.tsx                  /start
│   │   ├── train/new/page.tsx              ①
│   │   └── train/[id]/
│   │       ├── questions/page.tsx          ②
│   │       ├── readback/page.tsx           ③
│   │       ├── example/page.tsx            ④
│   │       ├── training/page.tsx           ⑤  (client, SSE)
│   │       └── ready/page.tsx              ⑥
│   ├── app/i/[slug]/page.tsx               the trained intern
│   ├── components/               ← Sheet, Button, Field, LedgerSlip, Stamp, DropZone,
│   │                               FileChip, StepRail, Table, Well, CellStrip
│   ├── lib/types.ts              ← ★ SHARED CONTRACT. write this first.
│   ├── mocks/events.json         ← ★ DEMO INSURANCE. write this first.
│   └── app/globals.css           ← tokens from 02-DESIGN-SYSTEM.md §2
├── api/                          ← AGENT: API owns this
│   ├── main.py                   FastAPI app, routes
│   ├── store.py                  SQLite, 5 tables
│   ├── jobs.py                   in-process job queue + event bus
│   ├── files.py                  upload, sniff, preview
│   └── schemas.py                pydantic ↔ types.ts, kept in sync BY HAND, check twice
├── engine/                       ← AGENT: LOOP owns this
│   ├── orchestrator.py           the loop itself
│   ├── planner.py                brief → questions → job_spec
│   ├── codegen.py                job_spec → script.py
│   ├── runner.py                 sandboxed execution
│   ├── scorer.py                 cell-level diff → score + structured findings
│   ├── repairer.py               findings → patch + plain-language line
│   ├── llm.py                    bedrock|anthropic|mock adapter
│   ├── events.py                 LoopEvent emitter
│   └── cli.py                    `python -m engine.cli train --fixture mock/`
├── guards/
│   └── no_llm_at_runtime.py      ← the claim, enforced
├── deploy/                       ← AGENT: INFRA owns this
│   ├── Dockerfile.web
│   ├── Dockerfile.api
│   ├── Dockerfile.tool-runtime
│   ├── docker-compose.yml
│   ├── pomerium/config.yaml
│   └── akash/deploy.sdl
├── mock/                         ← the fixture. see 06-MOCK-DATA.md
│   ├── manifest_2026-07-14.csv
│   ├── carrier_rates_2026-07.csv
│   ├── dispatch_summary_14.07.csv        ← ground truth
│   ├── manifest_2026-07-17.csv           ← "today's" files for the live demo
│   └── carrier_rates_2026-07b.csv
├── data/                         ← runtime. gitignored except .gitkeep
│   └── jobs/<job_id>/{inputs,expected,attempts,artifact}/
└── README.md                     ← architecture diagram + sponsors + how to run
```

## 3. Data model (SQLite, `data/intern.db`)

Five tables. Resist the sixth.

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,              -- uuid
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  slug TEXT UNIQUE,                 -- 'andrei-dispatch'
  brief TEXT NOT NULL,              -- his raw words, verbatim, never rewritten
  questions_json TEXT,              -- [{id, question, why, suggestions[], answer}]
  spec_json TEXT,                   -- the frozen job_spec. see 05 §4.3
  status TEXT NOT NULL,             -- draft|questioning|readback|example|training|ready|failed
  outcome TEXT,                     -- PERFECT|PLATEAU|BUDGET|FAILED
  best_score REAL,
  attempts_used INTEGER,
  train_ms INTEGER,
  created_at TEXT NOT NULL
);

CREATE TABLE files (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  role TEXT NOT NULL,               -- input|expected|today
  filename TEXT NOT NULL,
  path TEXT NOT NULL,               -- data/jobs/<job>/inputs/<file>
  bytes INTEGER,
  preview_json TEXT                 -- {columns[], rows[][], truncated}
);

CREATE TABLE attempts (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  n INTEGER NOT NULL,               -- 1-based
  score REAL,
  cells_ok INTEGER, cells_total INTEGER,
  strip TEXT,                       -- '1101111011…' one char per cell, for <CellStrip>
  findings_json TEXT,               -- structured. see 05 §5.4
  headline TEXT,                    -- the plain-language line on the slip
  changed TEXT,                     -- 'rounding on the Cost column'
  code_path TEXT,
  stdout TEXT, stderr TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL
);

CREATE TABLE runs (                 -- production runs of a trained intern
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL REFERENCES jobs(id),
  duration_ms INTEGER,
  ok INTEGER,
  created_at TEXT NOT NULL
);
```

`slug` is generated from the user's first name + a noun the planner extracts from the brief
(`dispatch`), deduped with `-2`. Andrei sees his own name in his own URL; that matters more
than it sounds.

## 4. Shared types — **write this file first, in the main thread, before fanning out**

`web/lib/types.ts` and `api/schemas.py` are the same objects in two languages. Every subagent
imports from these. Keeping them in sync is the main thread's job.

```typescript
// web/lib/types.ts

export type JobStatus =
  | "draft" | "questioning" | "readback" | "example" | "training" | "ready" | "failed";

export type Outcome = "PERFECT" | "PLATEAU" | "BUDGET" | "FAILED";

export interface Question {
  id: string;
  question: string;      // "If a truck isn't on the rate card, what do I do with that run?"
  why: string;           // "I can't work out a cost without a rate…"  ← always present
  suggestions: string[]; // 0–3 tappable answers
  answer?: string;
}

export interface SpecRule {
  n: number;
  text: string;          // "Throw away any run under 500 kg."  ← Andrei-language
  confidence: number;    // 0–1
  source: "said" | "asked" | "guessed";   // drives the "I'm guessing" block
}

export interface JobSpec {
  rules: SpecRule[];
  guesses: string[];     // ≥2 always, even when confident
  output_columns: string[];
  slug: string;
}

export interface Attempt {
  n: number;
  score: number;         // 0–1
  cells_ok: number;
  cells_total: number;
  strip: string;         // "1101111011…" — 1 = cell matches
  headline: string;      // "Sorted the rows the way you asked. One cost is a dollar off."
  changed: string;       // "rounding on the Cost column"
  duration_ms: number;
  at: string;            // ISO
}

export type LoopEvent =
  | { type: "phase";           phase: "WRITING" | "RUNNING" | "CHECKING" | "FIXING" }
  | { type: "attempt.started"; n: number }
  | { type: "attempt.scored";  attempt: Attempt }
  | { type: "converged";       outcome: Outcome; best: number; attempts: number; ms: number }
  | { type: "failed";          reason: string; hint: string }
  | { type: "log";             line: string };   // dev only, never rendered to Andrei
```

## 5. API

All JSON. All under `/api`. No versioning — it's a hackathon, and a `/v1` prefix is a lie
about the future.

| Method | Path | Body → Response |
|---|---|---|
| `POST` | `/api/session` | `{name,email}` → `{user}` + sets cookie |
| `POST` | `/api/jobs` | `{brief}` → `{job_id, questions[]}` — planner runs synchronously here, ~3s, show a phase label |
| `POST` | `/api/jobs/{id}/answers` | `{answers:{qid:text}}` → `{spec: JobSpec}` |
| `PATCH` | `/api/jobs/{id}/spec` | `{rules: SpecRule[]}` → `{spec}` — the read-back edit |
| `POST` | `/api/jobs/{id}/files` | multipart `role=input\|expected` → `{file, preview}` |
| `POST` | `/api/jobs/{id}/train` | `{}` → `202 {stream: "/api/jobs/{id}/events"}` |
| `GET` | `/api/jobs/{id}/events` | **SSE** stream of `LoopEvent` |
| `GET` | `/api/jobs/{id}` | → `{job, attempts[], spec}` — for refresh/back |
| `GET` | `/api/jobs/{id}/attempts/{n}/diff` | → `{expected, produced, wrong_cells[]}` |
| `GET` | `/api/jobs/{id}/artifact` | → `text/x-python` the produced script |
| `GET` | `/api/jobs/{id}/guard` | → `{pass, network_calls, model_calls, checked_at}` |
| `POST` | `/api/i/{slug}/run` | multipart 2 files → `{download_url, preview, ms}` |

### 5.9 The curl walkthrough — AGENT: API's definition of done

```bash
curl -c j -XPOST localhost:8000/api/session -d '{"name":"Andrei","email":"a@b.co"}'
JOB=$(curl -b j -XPOST localhost:8000/api/jobs -d @mock/brief.json | jq -r .job_id)
curl -b j -XPOST localhost:8000/api/jobs/$JOB/answers -d @mock/answers.json
curl -b j -F role=input    -F file=@mock/manifest_2026-07-14.csv    localhost:8000/api/jobs/$JOB/files
curl -b j -F role=input    -F file=@mock/carrier_rates_2026-07.csv  localhost:8000/api/jobs/$JOB/files
curl -b j -F role=expected -F file=@mock/dispatch_summary_14.07.csv localhost:8000/api/jobs/$JOB/files
curl -b j -XPOST localhost:8000/api/jobs/$JOB/train
curl -b j -N localhost:8000/api/jobs/$JOB/events     # watch scores climb
curl -b j localhost:8000/api/jobs/$JOB/guard         # {"pass":true,...}
curl -b j -F file=@mock/manifest_2026-07-17.csv -F file=@mock/carrier_rates_2026-07b.csv \
     localhost:8000/api/i/andrei-dispatch/run
```

## 6. Streaming

SSE, not WebSockets. One-directional, works through Pomerium with no config, survives a
proxy, and `EventSource` is four lines in the browser.

```python
# api/main.py
@app.get("/api/jobs/{job_id}/events")
async def events(job_id: str):
    async def gen():
        async for ev in bus.subscribe(job_id):          # asyncio.Queue per job
            yield f"data: {ev.model_dump_json()}\n\n"
        yield 'data: {"type":"done"}\n\n'
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})   # ← or nginx eats it
```

- **Replay on connect.** The bus keeps every event for a job in memory. A new subscriber gets
  the backlog first, then live. Andrei *will* refresh mid-training; if the Ledger comes back
  empty we look broken.
- Client reconnects with exponential backoff and dedupes by `attempt.n`.
- `type:"log"` events are dropped by the client unless `?dev=1`. Judges love `?dev=1`. Build it.

## 7. The sandbox

The generated script is untrusted code written by a model, executing on our box, on files a
stranger uploaded. Treat it that way even in a hackathon — and *say* you did, because
"we run model-written code safely" is the exact sentence Pomerium's judge wants to hear.

```python
# engine/runner.py — layered, cheapest first
def run(script_path, inputs, out_dir, timeout=20):
    """
    Layer 1  subprocess, never exec/eval in-process
    Layer 2  cwd = a fresh tempdir; only the input CSVs are copied in
    Layer 3  env = {} — no AWS_*, no ANTHROPIC_API_KEY, nothing inherited
    Layer 4  RLIMIT_CPU=10s, RLIMIT_AS=512MB, RLIMIT_NPROC=0, RLIMIT_FSIZE=32MB
    Layer 5  timeout=20s wall clock, SIGKILL the process group
    Layer 6  static check BEFORE running: AST-walk for socket/requests/urllib/httpx/
             subprocess/os.system/open(mode='w') outside out_dir/__import__/eval/exec
    Layer 7  (if time) docker run --network=none --read-only --memory=512m
                       --pids-limit=64 tool-runtime
    """
```

Layers 1–6 are **mandatory and take 40 minutes**. Layer 7 is the nice-to-have; if INFRA gets
there, the same `tool-runtime` image is what ships to Akash, so it's not wasted work.

Store `stdout`/`stderr` on the attempt row. The repairer needs the traceback; Andrei never
sees it.

## 8. Job execution

No Celery. No Redis. `asyncio.create_task` + an in-memory registry keyed by `job_id`.

- One training run at a time per job; a second `POST /train` returns the existing stream.
- Everything durable lands in SQLite as it happens, so a crash loses the stream but not the
  attempts. On reconnect the client fetches `GET /api/jobs/{id}` and rebuilds the Ledger.
- Wall-clock budget 180s, enforced by the orchestrator, not by the HTTP layer.

## 9. Producing and hosting the trained intern

On convergence the orchestrator writes:

```
data/jobs/<job_id>/artifact/
├── tool.py              the winning script, verbatim
├── requirements.txt     pinned: pandas==2.2.3  (nothing else. if the model adds a dep, reject)
├── spec.json            the frozen job_spec, for provenance
└── guard.json           the no-LLM check output
```

`/i/{slug}/run` copies the two uploaded files into a tempdir, invokes `tool.py` via the same
sandbox, returns the output. **Same runner as training** — the thing Andrei uses every day is
executed by the exact code path that scored it. No second implementation, no drift.

For the pitch: each artifact folder is a container image away from being its own Akash
deployment (`07-SPONSORS.md §4`). Today, one process hosts all of them, and that's an honest
answer to "how does it scale": *"identically, just with more containers."*

## 10. Config

```
LLM_PROVIDER=bedrock|anthropic|mock       default: bedrock
BEDROCK_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0
MAX_ATTEMPTS=6
WALL_CLOCK_MS=180000
PLATEAU_DELTA=0.02
PLATEAU_PATIENCE=2
SANDBOX_MODE=subprocess|docker            default: subprocess
ZERO_MODE=live|mock                       default: mock
NEXLA_MODE=live|mock                      default: mock
POMERIUM_ENABLED=true|false               default: false in dev
DEMO_FIXTURE=mock/                        the "Use the freight example" button
```

**Every sponsor defaults to mock.** You turn them on deliberately, one at a time, as each is
verified working. That is how you avoid discovering at 16:10 that a sponsor's staging
environment went down at 15:50.
