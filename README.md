# Intern — train an agent the way you'd train a new hire

> Build in progress — Loop Engineering Hackathon, AWS Builder Loft, 17 July 2026.

**The claim: the LLM is the trainer, not the worker.** The shipped tool has no model,
no network, no API key — enforced by `guards/no_llm_at_runtime.py`.

The loop: spec → codegen → sandboxed run → cell-level diff against the user's own
worked example → deterministic findings → repair → repeat until convergence.

Full spec in `docs/`. Fixture in `mock/`.

## Run it

```
docker compose up   →   http://localhost:3000   →   "Use the freight example"
```

Full README with architecture diagram lands before submission.
