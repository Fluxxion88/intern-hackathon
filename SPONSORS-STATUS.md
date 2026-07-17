# Sponsor status — audited 2026-07-17 ~14:25 PDT

| Sponsor | Where it's integrated | Mode | Proof |
|---|---|---|---|
| **Zero.xyz** | `engine/adapters/zero.py:40` (`resolve()` — live `zero search --json` + recorded replay in `recordings/zero_email_send.json`); hooked into the training path at `api/engine_bridge.py:~55` (on PERFECT convergence, discovers the email-transport capability, emits the "got a new skill · via Zero" event, visible with `?dev=1`) | **live-capable**, demo runs mock (replay of a real call) | Real discovery 2026-07-17 21:14: searchId `srch_jK9Mhpt11fl3hwK2lWS1o`, 23 capabilities, top hit StableEmail Send `z_dnUhpk.1` $0.02/call ($ verified again live in adapter test: `z_0rTvAf.1`). Log: `/tmp/zero-search.log` |
| **Nexla** | `api/adapters/nexla.py:24` (`register_intern()` — live via `nexla-cli login` + `sources create`, one trained intern → one Nexla flow) | **live-capable**, demo renders mock ("coming for your inbox next") | Real flow created 2026-07-17 21:18: source **id 125755, flow_id 634481**, `intern-andrei-dispatch-inbound`, status ACTIVE, org gmail.com-96b8ad1c. Log: `/tmp/nexla-create.log` |
| **Pomerium** | `deploy/pomerium/config.yaml:54` (per-intern route `/i/andrei-dispatch` with its own policy, `pass_identity_headers`); compose profile `pomerium` in `deploy/docker-compose.yml` | **live** in compose | Verified 2026-07-17: `COMPOSE_PROFILES=pomerium docker compose up` → GET `https://intern.localhost.pomerium.io/i/andrei-dispatch` returns **302 → authenticate.pomerium.app sign-in**. Identity enforced in front of the deployed intern. |
| **Akash** | `deploy/akash/deploy.sdl` (tool-runtime, **0.1 CPU / 128Mi / 128Mi**); app SDL for the judge-facing deployment in `deploy/akash/deploy-app.sdl` | SDL ready; console deploy in progress (TASK 2) | `docker compose build` of `intern-tool-runtime` smoke-tested end-to-end earlier today |

## The one sentence per judge

- **Zero**: "We are Zero's thesis pointed at a person instead of a developer — Zero unblocks the agent, we unblock the human, and neither of us asks anyone for an API key. Discovery happens at training time; what ships is inert."
- **Nexla**: "One trained intern is one Nexla flow — his inbox is the source, our artifact is the transform, his folder is the destination. We created that flow on your platform today: id 634481."
- **Pomerium**: "We execute model-written code on files a stranger uploaded for someone who can't read the code — the agent writes the code, but it doesn't decide what the code may reach. That's policy, it lives outside the model, and Pomerium enforces it (and the per-intern route means his drivers see his intern, nobody else's)."
- **Akash**: "We're the cheapest workload you'll see today, on purpose — 0.1 CPU, no GPU, no model, 1-second runs. A trained intern is a rounding error and Akash prices it like one. That IS why $20-once works."

## Boundary note (say it if asked)

Zero and Nexla touch **transport**, never the transform: the shipped artifact still
makes zero network calls and `guards/no_llm_at_runtime.py` stays green. Discovery
and delivery are training-time / platform-side; the tool that runs every morning
is inert. That boundary is the product.
