# INTERN — Start Here

> **You are Claude Fable 5 running in Claude Code with a large context window.**
> This folder is the complete specification for a hackathon build. Read it all before
> writing a single line of code. Total read cost is ~40k tokens. You have room.

---

## 1. Read order (mandatory)

| # | File | What it gives you |
|---|------|-------------------|
| 00 | `00-START-HERE.md` | This file. Orchestration, rules, definition of done. |
| 01 | `01-PRODUCT.md` | What we're building, for whom, the one demo story, scope fence. |
| 02 | `02-DESIGN-SYSTEM.md` | Tokens, type, shadows, components. Non-negotiable visual law. |
| 03 | `03-SCREENS.md` | Every screen, wireframed, with final copy. |
| 04 | `04-ARCHITECTURE.md` | Services, data model, API, sandbox, deployment. |
| 05 | `05-LOOP-ENGINE.md` | The heart. plan → act → observe → self-correct. Scoring. Prompts. |
| 06 | `06-MOCK-DATA.md` | The demo fixture. The 7 hidden rules. |
| 07 | `07-SPONSORS.md` | Zero.xyz, Pomerium, Akash, Nexla integration points. |
| 08 | `08-BUILD-PLAN.md` | Task graph, subagent assignments, timeline, cut-list. |

---

## 2. The one-sentence product

**Intern lets a non-technical office professional describe a repetitive file chore in
plain language and walk away with a deployed, deterministic web tool that does it —
trained by an LLM loop against their own worked example.**

## 3. The one claim that wins this hackathon

> **The LLM is the trainer, not the worker.**

The agent loop writes, runs, scores, and repairs a **pure Python script**. When training
converges, the model is removed. The shipped tool contains **zero LLM calls at runtime**.
It is deterministic, auditable, instant, and costs cents to host.

Every design decision in this spec serves that claim. If you find yourself putting an LLM
call inside the produced artifact, you have broken the product. Don't.

## 4. Hard rules for you, the implementing agent

1. **No LLM at runtime in the produced tool.** Training-time only. Enforced by a static
   check (`guards/no_llm_at_runtime.py`) that greps the generated script for network/LLM
   imports and fails the build. See `05-LOOP-ENGINE.md §9`.
2. **The demo must work offline-ish.** Every sponsor integration is behind an adapter with
   a `MOCK_MODE` fallback. If Zero/Pomerium/Akash is down at 16:00, the demo still runs.
   Never let a sponsor SDK be on the critical path of the happy path.
3. **Follow `02-DESIGN-SYSTEM.md` literally.** Do not invent colors. Do not add a purple
   gradient. Do not add a border-radius above 4px anywhere except the Stamp. There is no
   accent color and that is the point.
4. **Copy is spec.** Strings in `03-SCREENS.md` are final. Do not rewrite them to be
   friendlier. They were written to be plain.
5. **Ship vertical, not horizontal.** A working Brief→Read-back→Training→First-day path
   beats a beautiful settings page. Follow the cut-list in `08-BUILD-PLAN.md`.
6. **Commit often, small messages.** Public GitHub repo is a submission requirement.
7. **When blocked >10 minutes on a sponsor SDK, switch its adapter to MOCK_MODE, commit,
   move on, and leave a `TODO(sponsor)` comment.** Time is the scarcest resource.

## 5. Subagent orchestration

Run these as parallel Task subagents. Each owns files nobody else touches. The contract
between them is the OpenAPI schema in `04-ARCHITECTURE.md §5` and the TypeScript types in
`web/lib/types.ts` — write those **first, together, in the main thread**, then fan out.

```
                         ┌──────────────────────────────┐
                         │  MAIN THREAD (you)           │
                         │  - read all docs             │
                         │  - scaffold repo             │
                         │  - write types.ts + schemas  │
                         │  - write mock fixtures       │
                         └───────────────┬──────────────┘
                                         │ fan out
            ┌────────────────┬───────────┴──────┬─────────────────┐
            ▼                ▼                  ▼                 ▼
    ┌───────────────┐ ┌──────────────┐ ┌────────────────┐ ┌──────────────┐
    │ AGENT: LOOP   │ │ AGENT: API   │ │ AGENT: WEB     │ │ AGENT: INFRA │
    │ engine/       │ │ api/         │ │ web/           │ │ deploy/      │
    │ - planner     │ │ - FastAPI    │ │ - Next.js      │ │ - Dockerfile │
    │ - codegen     │ │ - SSE stream │ │ - design sys   │ │ - pomerium   │
    │ - runner      │ │ - SQLite     │ │ - 6 screens    │ │ - akash SDL  │
    │ - scorer      │ │ - job queue  │ │ - Ledger UI    │ │ - compose    │
    │ - repairer    │ │              │ │                │ │              │
    │ spec: 05, 06  │ │ spec: 04     │ │ spec: 02, 03   │ │ spec: 07     │
    └───────────────┘ └──────────────┘ └────────────────┘ └──────────────┘
            │                │                  │                 │
            └────────────────┴─────────┬────────┴─────────────────┘
                                       ▼
                         ┌──────────────────────────────┐
                         │  MAIN THREAD: integrate      │
                         │  - wire SSE → Ledger         │
                         │  - run E2E on mock fixture   │
                         │  - record demo               │
                         └──────────────────────────────┘
```

### Subagent briefs (paste these verbatim)

**AGENT: LOOP**
> Read `docs/05-LOOP-ENGINE.md` and `docs/06-MOCK-DATA.md` in full. Implement `engine/`
> exactly as specced: `planner.py`, `codegen.py`, `runner.py`, `scorer.py`, `repairer.py`,
> `orchestrator.py`. You own only `engine/` and `tests/engine/`. Your definition of done:
> `python -m engine.cli train --fixture mock/ --max-attempts 6` prints a rising score and
> converges to ≥0.95 on the fixture in `06-MOCK-DATA.md`. Emit every event as JSON on
> stdout per the `LoopEvent` schema. Do not touch the API or the web app.

**AGENT: API**
> Read `docs/04-ARCHITECTURE.md` in full. Implement `api/` — FastAPI, SQLite, the endpoints
> in §5, SSE streaming in §6, and the file-serving for deployed tools in §7. Import the
> engine as a library; never reimplement it. You own only `api/` and `tests/api/`. Definition
> of done: `curl` walkthrough in §5.9 passes end-to-end against a stubbed engine.

**AGENT: WEB**
> Read `docs/02-DESIGN-SYSTEM.md` and `docs/03-SCREENS.md` in full — they are law, follow
> them literally, including copy. Implement `web/` — Next.js 15 App Router, Tailwind v4,
> no component library. Build the token layer first (§2 of the design system), then the six
> screens. Use the SSE contract from `04-ARCHITECTURE.md §6`; if the API isn't up, drive the
> UI from `web/mocks/events.json`. You own only `web/`. Definition of done: all six screens
> render at 1440px and 390px, keyboard-navigable, and the Ledger animates from mock events.

**AGENT: INFRA**
> Read `docs/07-SPONSORS.md` in full. Deliver `deploy/`: multi-stage Dockerfiles for api and
> web, `docker-compose.yml` with Pomerium in front, `deploy/akash/deploy.sdl`, and the
> `tool-runtime` image that hosts a produced tool. You own only `deploy/` and `infra/`.
> Definition of done: `docker compose up` serves the app through Pomerium on localhost with
> a working identity header, and `deploy.sdl` passes `provider-services tx validate`.

## 6. Definition of done (16:00 hard stop)

- [ ] Public GitHub repo, README with architecture diagram and sponsor list
- [ ] `docker compose up` → working app
- [ ] Live demo path: Brief → Read-back → upload 3 mock files → watch loop → deployed tool → drop 2 files → get 1 back
- [ ] Ledger shows ≥4 attempts with rising accuracy, and the produced script visible/downloadable
- [ ] `guards/no_llm_at_runtime.py` passes and is shown in the demo
- [ ] ≥3 sponsors genuinely integrated (target: Zero, Pomerium, Akash, Nexla)
- [ ] 3-minute demo video recorded
- [ ] Devpost submitted with all teammates attached

## 7. Anti-goals — do not build these

Auth/registration beyond a mocked session · Payments · Teams/orgs · A tool marketplace ·
Multi-tenant isolation beyond a directory per job · Model choice UI · Dark mode toggle ·
i18n · A settings page · Anything with the word "dashboard" in it.
