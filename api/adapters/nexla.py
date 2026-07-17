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
        """One trained intern → one Nexla flow (inbox source → run → destination)."""
        inbox = f"{slug}@in.intern.works"
        if self.mode == "mock":
            return {"mode": "mock", "inbox": inbox, "flow_id": None,
                    "note": "coming for your inbox next"}
        # TODO(sponsor): live flow registration via the Nexla API once the
        # service-key auth path is confirmed.
        raise NotImplementedError("NEXLA_MODE=live not wired; use mock")
