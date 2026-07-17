"""Nexla adapter — the intern's inbox and outbox.

One trained intern → one Nexla flow. Source: his inbox
(andrei-dispatch@in.intern.works). Destination: wherever his summaries already
go. The transform in the middle is our artifact — we are a step in their
pipeline, and that is exactly the right shape for both products.

NEXLA_MODE=mock (default): /i/[slug] renders the email address greyed with
"coming for your inbox next". TODO(sponsor): the dev express-code endpoint
(NEXLA_API_URL) returned 404 on the /token probe — confirm the service-key
auth path with the Nexla judges (Abhijit/Amey), then flip NEXLA_MODE=live.
"""
from __future__ import annotations

import os


class NexlaAdapter:
    def __init__(self, mode: str | None = None):
        self.mode = mode or os.environ.get("NEXLA_MODE", "mock")
        self.api_url = os.environ.get("NEXLA_API_URL", "")
        self.service_key = os.environ.get("NEXLA_SERVICE_KEY", "")

    def register_intern(self, slug: str, spec: dict) -> dict:
        """One trained intern → one Nexla flow (inbox source → run → destination).

        live: real calls via nexla-cli (service-key → bearer token → webhook
        source). Proven 2026-07-17: created source id 125755 / flow_id 634481
        ("intern-andrei-dispatch-inbound", ACTIVE) on the Nexla dev org.
        mock: /i/[slug] renders the email line greyed, "coming for your inbox next".
        """
        inbox = f"{slug}@in.intern.works"
        if self.mode == "mock":
            return {"mode": "mock", "inbox": inbox, "flow_id": None,
                    "note": "coming for your inbox next"}
        import subprocess
        token = subprocess.run(
            ["nexla-cli", "login", "--service-key", self.service_key],
            capture_output=True, text=True, timeout=30,
        ).stdout.splitlines()[0].strip()
        out = subprocess.run(
            ["nexla-cli", "sources", "create",
             "--name", f"intern-{slug}-inbound", "--connector", "webhook",
             "--description",
             f"Inbound files for {slug} (intern.works/i/{slug}); the trained "
             f"artifact transforms, the summary goes back."],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "NEXLA_TOKEN": token},
        )
        import json as _json
        d = _json.loads(out.stdout)
        return {"mode": "live", "inbox": inbox, "flow_id": d.get("flow_id"),
                "source_id": d.get("id"), "status": d.get("status")}
