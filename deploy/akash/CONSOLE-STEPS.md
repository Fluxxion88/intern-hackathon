# Akash Console — exact steps (5–10 min of clicking)

Everything is pre-validated: both images are public on Docker Hub (amd64), and
the exact two-service topology in `deploy-app.sdl` was run locally end-to-end
(web → api by service name, seeded intern, file-drop returns the correct CSV).

1. Open https://console.akash.network → sign in (wallet or the credit-card /
   trial path — we have the $250 hackathon credits; redeem code from the Akash
   Discord if not already applied).
2. **Deployments → Deploy → Run Custom Container / Upload SDL.**
3. Paste the full contents of `deploy/akash/deploy-app.sdl` (repo root:
   `deploy/akash/deploy-app.sdl`). No edits needed — image refs
   `fluxxion88/intern-api:demo` and `fluxxion88/intern-web:demo` are already
   pushed and public; env is `LLM_PROVIDER=mock`, `SEED_DEMO=1` (no keys
   anywhere in the SDL — by design).
4. Create deployment → accept the deposit (5 AKT-equivalent from credits).
5. Wait for **bids** (~30–60s) → pick a cheap bid from a named provider with
   good uptime → **Accept / Create lease**.
6. Lease page → wait for both services to show **Available: 1** (api seeds
   itself in ~1s on boot; first web boot ~10s).
7. Copy the **URI** the provider assigned to the `web` service (the one with
   global expose on port 80). That's the judge URL.
8. Smoke test, in this order:
   - `<uri>/` → landing page with the looping Ledger hero
   - `<uri>/i/andrei-dispatch` → the trained intern; drop
     `mock/manifest_2026-07-17.csv` + `mock/carrier_rates_2026-07b.csv`
     (any order) → summary CSV back in well under a second
   - Stretch (full flow, all mock): `/start` → sign in → "Use the freight
     example" → 3 answers → approve → upload the three 14.07 mock files →
     watch the Ledger replay 68 → 96 → 100 → stamp
9. Paste the URI into the Devpost submission and DEMO.md.

If a provider rejects the manifest: re-open the deployment → Update → try
another bid. If `web` serves but pages 500: check the `api` service logs in the
lease view — it must show `seed: andrei-dispatch ready — 3 attempts, best 1.0`.

Fallbacks (in order): any Docker-capable host — 
`docker run -d -e LLM_PROVIDER=mock -e SEED_DEMO=1 fluxxion88/intern-api:demo`
+ `docker run -d -p 80:3000 fluxxion88/intern-web:demo` on one network with the
api aliased as `api`. Or demo entirely locally — the recorded video is the
primary artifact; the public URL is a bonus.

## LIVE DEPLOYMENT (deployed via Console API, 2026-07-17 ~14:45)

- **Public URL: http://c1v988lc4p93nd394caog9pvrg.ingress.cpu.dal.aes.akash.pub**
- dseq `1784325409922` · provider `provider.cpu.dal.aes.akash.pub` (US-Missouri, 99.5% uptime) · ~$0.03/day
- Smoke-tested externally: landing 200, /i/andrei-dispatch file-drop → TOTAL 17.11 / 4,368, training replay plays to MATCHED
- Close when done: `curl -X DELETE https://console-api.akash.network/v1/deployments/1784325409922 -H "x-api-key: $AKASH_API_KEY"`
