# Read the spec first

Everything you need is in `docs/`. Read them in order — all of them — before writing code.

1. `docs/00-START-HERE.md`   ← orchestration, hard rules, definition of done
2. `docs/01-PRODUCT.md`      ← who, why, the one demo story, scope fence
3. `docs/02-DESIGN-SYSTEM.md`← tokens/type/shadows. LAW.
4. `docs/03-SCREENS.md`      ← every screen + final copy. LAW.
5. `docs/04-ARCHITECTURE.md` ← services, data model, API, sandbox
6. `docs/05-LOOP-ENGINE.md`  ← the heart. read twice.
7. `docs/06-MOCK-DATA.md`    ← the fixture in `mock/` (already generated & verified)
8. `docs/07-SPONSORS.md`     ← Zero / Pomerium / Akash / Nexla + the 3-min demo script
9. `docs/08-BUILD-PLAN.md`   ← task graph, hard gates, cut-list

## The one claim

**The LLM is the trainer, not the worker.** The shipped tool contains zero LLM calls.
If you put a model call inside the produced artifact, you have broken the product.

## Build order (main thread)

1. Read all of `docs/`.
2. Scaffold the repo per `04-ARCHITECTURE.md §2`.
3. Write `web/lib/types.ts` + `api/schemas.py` + `web/mocks/events.json` — the contract.
4. `git init`, public repo, push.
5. Fan out the four subagent briefs in `00-START-HERE.md §5`.
6. Build the scorer first. It is the ground everything else stands on.
