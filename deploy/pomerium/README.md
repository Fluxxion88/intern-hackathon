# Pomerium — the intern's badge

Threat model in 5 lines:

1. We execute code **written by a language model**, on **files a stranger uploaded**, on **our infrastructure**, for **someone who cannot read the code** — every clause is a reason to gate access.
2. Pomerium fronts everything (`:443`); web, API and each trained intern are separate routes with separate policies — Andrei gets the app, only `@andrei-freight.com` gets `/i/andrei-dispatch`.
3. `pass_identity_headers` injects `X-Pomerium-Jwt-Assertion`; the API reads identity from that header and **never trusts a client-supplied user id**.
4. The generated tool runs with `env={}` and no network — when a tool legitimately needs egress (the Zero email path), it goes **through Pomerium as an egress policy point**, not around it: the agent writes the code, it doesn't get to decide what the code may reach.
5. Local dev runs with `POMERIUM_ENABLED=false` (app works bare); the recording flips it on via `COMPOSE_PROFILES=pomerium docker compose up`, using `*.localhost.pomerium.io` (public DNS → 127.0.0.1) + Pomerium's hosted authenticate.

Bring it up: `cd deploy && COMPOSE_PROFILES=pomerium docker compose up`, then open `https://intern.localhost.pomerium.io` (self-signed cert warning is expected locally).

TODO(sponsor): the config uses Pomerium's hosted authenticate (`authenticate.pomerium.app`) so login works with zero IdP setup; a self-hosted authenticate block (docs/07 §3 verbatim shape) is included commented-out and needs real OAuth client creds. Docker daemon was down at build time, so `pomerium verify` of the container was not run — config is YAML-lint clean and follows the documented route schema.
