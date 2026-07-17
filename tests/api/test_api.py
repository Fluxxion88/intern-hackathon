"""The §5.9 curl walkthrough as a pytest, against the ASGI app in-process.

Run:  .venv/bin/python -m pytest tests/api -q
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MOCK = REPO_ROOT / "mock"

# Must be set BEFORE the app/store are imported by fixtures.
_TMP = tempfile.mkdtemp(prefix="intern-test-")
os.environ["INTERN_DATA_DIR"] = _TMP
os.environ["STUB_SLEEP_SCALE"] = "0"

from api import store  # noqa: E402
from api.main import app  # noqa: E402


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def client():
    store.init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport,
                                 base_url="http://testserver") as c:
        yield c


async def make_session(client: httpx.AsyncClient) -> dict:
    # exactly like curl: JSON body with a form content-type
    r = await client.post("/api/session",
                          content='{"name":"Andrei","email":"a@b.co"}',
                          headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200, r.text
    assert "intern_session" in r.cookies
    return r.json()["user"]


async def make_trained_job(client: httpx.AsyncClient) -> tuple[str, str]:
    """brief → answers → 3 files → train → drain events. Returns (job_id, slug)."""
    brief = json.loads((MOCK / "brief.json").read_text())
    r = await client.post("/api/jobs", json=brief)
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]

    answers = json.loads((MOCK / "answers.json").read_text())
    r = await client.post(f"/api/jobs/{job_id}/answers", json=answers)
    assert r.status_code == 200, r.text
    slug = r.json()["spec"]["slug"]

    for role, fname in [("input", "manifest_2026-07-14.csv"),
                        ("input", "carrier_rates_2026-07.csv"),
                        ("expected", "dispatch_summary_14.07.csv")]:
        r = await client.post(f"/api/jobs/{job_id}/files", data={"role": role},
                              files={"file": (fname, (MOCK / fname).read_bytes(), "text/csv")})
        assert r.status_code == 200, r.text

    r = await client.post(f"/api/jobs/{job_id}/train")
    assert r.status_code == 202
    assert r.json()["stream"] == f"/api/jobs/{job_id}/events"

    # second POST /train returns the same stream, no second run
    r2 = await client.post(f"/api/jobs/{job_id}/train")
    assert r2.status_code == 202
    assert r2.json()["stream"] == r.json()["stream"]

    # drain the SSE stream (STUB_SLEEP_SCALE=0 → completes immediately)
    events = []
    async with client.stream("GET", f"/api/jobs/{job_id}/events") as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert resp.headers["cache-control"] == "no-cache"
        assert resp.headers["x-accel-buffering"] == "no"
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    # real engine emits attempt.started then phase:WRITING; the stub reversed
    # the pair — either order is contract-valid, the reducer keys on type
    assert {e["type"] for e in events[:2]} == {"phase", "attempt.started"}
    assert {"type": "phase", "phase": "WRITING"} in events[:2] or \
           {"type": "attempt.started", "n": 1} in events[:2]
    scored = [e for e in events if e["type"] == "attempt.scored"]
    assert len(scored) >= 3
    assert max(e["attempt"]["score"] for e in scored) >= 0.99
    conv = [e for e in events if e["type"] == "converged"]
    assert conv and conv[0]["outcome"] == "PERFECT"
    assert events[-1] == {"type": "done"}
    return job_id, slug


@pytest.mark.anyio
async def test_walkthrough(client: httpx.AsyncClient):
    user = await make_session(client)
    assert user["name"] == "Andrei"

    job_id, slug = await make_trained_job(client)
    assert slug.startswith("andrei-dispatch")

    # SSE replay: a SECOND subscriber after convergence gets the full backlog
    replay = []
    async with client.stream("GET", f"/api/jobs/{job_id}/events") as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                replay.append(json.loads(line[6:]))
    assert len([e for e in replay if e["type"] == "attempt.scored"]) == 5
    assert replay[-1] == {"type": "done"}

    # GET job — refresh/rebuild path
    r = await client.get(f"/api/jobs/{job_id}")
    body = r.json()
    assert body["job"]["status"] == "ready"
    assert body["job"]["outcome"] == "PERFECT"
    assert len(body["attempts"]) == 5
    assert body["spec"]["slug"] == slug
    assert len(body["spec"]["rules"]) == 8

    # diff
    r = await client.get(f"/api/jobs/{job_id}/attempts/1/diff")
    assert r.status_code == 200
    d = r.json()
    assert d["expected"]["columns"] == ["Date", "Route", "Truck", "Load (t)", "Cost ($)"]
    assert d["produced"]["columns"] == d["expected"]["columns"]
    assert len(d["wrong_cells"]) == 30  # 50 cells, 20 ok on attempt 1

    # artifact
    r = await client.get(f"/api/jobs/{job_id}/artifact")
    assert r.status_code == 200
    assert "text/x-python" in r.headers["content-type"]
    assert "pandas" in r.text

    # guard
    r = await client.get(f"/api/jobs/{job_id}/guard")
    g = r.json()
    assert g["pass"] is True
    assert g["network_calls"] == 0 and g["model_calls"] == 0

    # run the trained intern on today's files
    r = await client.post(
        f"/api/i/{slug}/run",
        files=[("file", ("manifest_2026-07-17.csv",
                         (MOCK / "manifest_2026-07-17.csv").read_bytes(), "text/csv")),
               ("file", ("carrier_rates_2026-07b.csv",
                         (MOCK / "carrier_rates_2026-07b.csv").read_bytes(), "text/csv"))])
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["ms"] >= 0
    assert out["preview"]["columns"] == ["Date", "Route", "Truck", "Load (t)", "Cost ($)"]
    assert out["preview"]["rows"][-1][2] == "TOTAL"

    r = await client.get(out["download_url"])
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert r.text.startswith("Date,Route,Truck")


@pytest.mark.anyio
async def test_patch_spec_and_auth(client: httpx.AsyncClient):
    # no cookie → 401
    r = await client.post("/api/jobs", json={"brief": "x"})
    assert r.status_code == 401

    await make_session(client)
    r = await client.post("/api/jobs", json={"brief": "merge my freight manifest"})
    job_id = r.json()["job_id"]
    assert len(r.json()["questions"]) == 3
    assert all(q["why"] for q in r.json()["questions"])

    # PATCH before answers → 409
    r = await client.patch(f"/api/jobs/{job_id}/spec", json={"rules": [
        {"n": 1, "text": "x", "confidence": 1.0, "source": "said"}]})
    assert r.status_code == 409

    await client.post(f"/api/jobs/{job_id}/answers", json={"answers": {"q1": "Under 500 kg."}})
    r = await client.patch(f"/api/jobs/{job_id}/spec", json={"rules": [
        {"n": 1, "text": "Sort by destination first.", "confidence": 1.0, "source": "said"}]})
    assert r.status_code == 200
    assert r.json()["spec"]["rules"][0]["text"] == "Sort by destination first."

    # answered questions were stored
    r = await client.get(f"/api/jobs/{job_id}")
    assert r.json()["job"]["status"] == "readback"


@pytest.mark.anyio
async def test_slug_dedupe(client: httpx.AsyncClient):
    await make_session(client)
    r1 = await client.post("/api/jobs", json={"brief": "dispatch summary for my drivers"})
    r2 = await client.post("/api/jobs", json={"brief": "dispatch summary for my drivers"})
    s1 = (await client.get(f"/api/jobs/{r1.json()['job_id']}")).json()["job"]["slug"]
    s2 = (await client.get(f"/api/jobs/{r2.json()['job_id']}")).json()["job"]["slug"]
    assert s1 != s2
    assert s1.startswith("andrei-dispatch") and s2.startswith("andrei-dispatch")
