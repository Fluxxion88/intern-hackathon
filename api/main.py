"""FastAPI app — all routes from docs/04-ARCHITECTURE.md §5.

Start from repo root:  .venv/bin/python -m uvicorn api.main:app --port 8000
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.datastructures import UploadFile as StarletteUploadFile

from api import engine_stub, files as files_mod, jobs as jobs_mod, store
from api.schemas import GuardReport, JobSpec, Question, SpecRule

# ── app ────────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    store.init_db()
    yield


app = FastAPI(title="intern.works API", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── session / auth ─────────────────────────────────────────────────────

SECRET = b"intern-dev-secret-2026"  # hardcoded dev secret, fine per spec
COOKIE = "intern_session"


def _sign(user_id: str) -> str:
    sig = hmac.new(SECRET, user_id.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{user_id}.{sig}"


def _verify(token: Optional[str]) -> Optional[str]:
    if not token or "." not in token:
        return None
    user_id, sig = token.rsplit(".", 1)
    if hmac.compare_digest(_sign(user_id), f"{user_id}.{sig}"):
        return user_id
    return None


def current_user(request: Request) -> dict:
    user_id = _verify(request.cookies.get(COOKIE))
    user = store.get_user(user_id) if user_id else None
    if not user:
        raise HTTPException(401, "No session. POST /api/session first.")
    return user


async def json_body(request: Request) -> dict:
    """Lenient JSON parse — the §5.9 curl walkthrough posts JSON with
    Content-Type: application/x-www-form-urlencoded, so never trust the header."""
    raw = await request.body()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(400, "Body must be JSON")


@app.post("/api/session")
async def create_session(request: Request, response: Response):
    body = await json_body(request)
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    if not name or not email:
        raise HTTPException(400, "name and email are required")
    user = store.create_user(name, email)
    response.set_cookie(COOKIE, _sign(user["id"]), httponly=True, samesite="lax",
                        max_age=60 * 60 * 24 * 7, path="/")
    return {"user": user}


# ── planner (canned until the real engine lands) ───────────────────────

CANNED_QUESTIONS = [
    {
        "id": "q1",
        "question": "What counts as a small load?",
        "why": "You said to skip the little stuff, but I need a number to draw the line at.",
        "suggestions": ["Under 500 kg.", "Under 1 tonne.", "Don't skip anything."],
    },
    {
        "id": "q2",
        "question": "If a carrier isn't on the rate card, drop the row or flag it?",
        "why": "I can't work out a cost without a rate, so I need to know what to do with those runs.",
        "suggestions": ["Keep it, mark the cost as TBC.", "Drop the row.", "Stop and ask me."],
    },
    {
        "id": "q3",
        "question": "Should the file be dated, and in what format?",
        "why": "Your example summary has the date in its name; I want to name mine the same way.",
        "suggestions": ["Name it with the date, like the summary I'm giving you.",
                        "Same name every day.", "No date in the name."],
    },
]

# NOTE: docs/05 §4.3 shows rule 7 with source "inferred"; the frozen schema only
# allows said|asked|guessed, so it is mapped to "guessed" here.
CANNED_RULES = [
    {"n": 1, "text": "Take two files from you: the day's manifest and the current rate card.",
     "confidence": 1.0, "source": "said"},
    {"n": 2, "text": "Throw away any run under 500 kg.", "confidence": 1.0, "source": "asked"},
    {"n": 3, "text": "Match each run to its truck's rate. If the truck isn't on the card, "
             "keep the run and write \"TBC\" where the cost goes.",
     "confidence": 1.0, "source": "asked"},
    {"n": 4, "text": "Work out the cost: the base fee, plus the rate per km times the distance. "
             "Round to whole dollars.", "confidence": 0.9, "source": "said"},
    {"n": 5, "text": "Turn kilos into tonnes, two decimal places.", "confidence": 0.85, "source": "said"},
    {"n": 6, "text": "Sort by destination A→Z, then dearest run first.", "confidence": 0.8, "source": "said"},
    {"n": 7, "text": "Name the columns your way: Date, Route, Truck, Load (t), Cost ($).",
     "confidence": 0.7, "source": "guessed"},
    {"n": 8, "text": "Put a TOTAL row at the bottom with the load and the cost added up, "
             "and nothing in the other columns.", "confidence": 0.9, "source": "said"},
]

CANNED_GUESSES = [
    "Dates like 17.07.2026, because that's how your files are written.",
    "A comma in the thousands, no cents.",
]

OUTPUT_COLUMNS = ["Date", "Route", "Truck", "Load (t)", "Cost ($)"]

NOUN_MAP = [
    (("dispatch", "driver", "manifest", "carrier", "truck", "freight", "haul"), "dispatch"),
    (("invoice", "billing"), "invoices"),
    (("report",), "reports"),
    (("summary",), "summary"),
]


def make_slug(user_name: str, brief: str) -> str:
    first = re.sub(r"[^a-z0-9]", "", (user_name.split() or ["intern"])[0].lower()) or "intern"
    low = brief.lower()
    noun = "desk"
    for keys, val in NOUN_MAP:
        if any(k in low for k in keys):
            noun = val
            break
    base = f"{first}-{noun}"
    slug, i = base, 2
    while store.slug_exists(slug):
        slug = f"{base}-{i}"
        i += 1
    return slug


def job_public(job: dict) -> dict:
    return {"id": job["id"], "slug": job["slug"], "brief": job["brief"],
            "status": job["status"], "outcome": job["outcome"],
            "best_score": job["best_score"], "attempts_used": job["attempts_used"],
            "train_ms": job["train_ms"], "created_at": job["created_at"]}


def get_job_or_404(job_id: str) -> dict:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job


# ── jobs ───────────────────────────────────────────────────────────────

@app.post("/api/jobs")
async def create_job(request: Request, user: dict = Depends(current_user)):
    body = await json_body(request)
    brief = (body.get("brief") or "").strip()
    if not brief:
        raise HTTPException(400, "brief is required")
    slug = make_slug(user["name"], brief)
    questions = [Question(**q).model_dump() for q in CANNED_QUESTIONS]
    job = store.create_job(user["id"], brief, slug, questions)
    return {"job_id": job["id"], "questions": questions}


@app.post("/api/jobs/{job_id}/answers")
async def submit_answers(job_id: str, request: Request, user: dict = Depends(current_user)):
    job = get_job_or_404(job_id)
    body = await json_body(request)
    answers: dict = body.get("answers") or {}
    questions = json.loads(job["questions_json"] or "[]")
    for q in questions:
        if q["id"] in answers:
            q["answer"] = str(answers[q["id"]])
    spec = JobSpec(rules=[SpecRule(**r) for r in CANNED_RULES],
                   guesses=CANNED_GUESSES, output_columns=OUTPUT_COLUMNS,
                   slug=job["slug"]).model_dump()
    store.update_job(job_id, questions_json=json.dumps(questions),
                     spec_json=json.dumps(spec), status="readback")
    return {"spec": spec}


@app.patch("/api/jobs/{job_id}/spec")
async def patch_spec(job_id: str, request: Request, user: dict = Depends(current_user)):
    job = get_job_or_404(job_id)
    if not job["spec_json"]:
        raise HTTPException(409, "no spec yet — answer the questions first")
    body = await json_body(request)
    rules = body.get("rules")
    if not isinstance(rules, list) or not rules:
        raise HTTPException(400, "rules: SpecRule[] is required")
    spec = json.loads(job["spec_json"])
    spec["rules"] = [SpecRule(**r).model_dump() for r in rules]
    spec = JobSpec(**spec).model_dump()
    store.update_job(job_id, spec_json=json.dumps(spec))
    return {"spec": spec}


@app.post("/api/jobs/{job_id}/files")
async def upload_file(job_id: str, request: Request, user: dict = Depends(current_user)):
    get_job_or_404(job_id)
    form = await request.form()
    role = str(form.get("role") or "input")
    if role not in ("input", "expected", "today"):
        raise HTTPException(400, "role must be input|expected|today")
    up = form.get("file")
    if not isinstance(up, StarletteUploadFile):
        raise HTTPException(400, "multipart field 'file' is required")
    raw = await up.read()
    rec, preview = files_mod.save_upload(job_id, role, up.filename or "upload.csv", raw)
    file_obj = {"id": rec["id"], "role": role, "filename": rec["filename"],
                "bytes": rec["bytes"], "preview": preview}
    if role == "expected":
        store.update_job(job_id, status="example")
    return {"file": file_obj, "preview": preview}


@app.post("/api/jobs/{job_id}/train")
async def train(job_id: str, user: dict = Depends(current_user)):
    get_job_or_404(job_id)
    jobs_mod.start_training(job_id)  # idempotent: 2nd POST returns the same stream
    return JSONResponse(status_code=202,
                        content={"stream": f"/api/jobs/{job_id}/events"})


@app.get("/api/jobs/{job_id}/events")
async def events(job_id: str, user: dict = Depends(current_user)):
    get_job_or_404(job_id)
    jobs_mod.replay_or_rebuild(job_id)  # process restarted? rebuild backlog from SQLite

    async def gen():
        async for ev in jobs_mod.bus.subscribe(job_id):
            yield f"data: {jobs_mod.event_json(ev)}\n\n"
        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(current_user)):
    job = get_job_or_404(job_id)
    attempts = [{"n": a["n"], "score": a["score"], "cells_ok": a["cells_ok"],
                 "cells_total": a["cells_total"], "strip": a["strip"],
                 "headline": a["headline"], "changed": a["changed"],
                 "duration_ms": a["duration_ms"], "at": a["created_at"]}
                for a in store.get_attempts(job_id)]
    spec = json.loads(job["spec_json"]) if job["spec_json"] else None
    return {"job": job_public(job), "attempts": attempts, "spec": spec}


@app.get("/api/jobs/{job_id}/attempts/{n}/diff")
async def attempt_diff(job_id: str, n: int, user: dict = Depends(current_user)):
    get_job_or_404(job_id)
    attempt = store.get_attempt(job_id, n)
    if not attempt:
        raise HTTPException(404, "attempt not found")
    expected_files = store.get_files(job_id, role="expected")
    expected = ({"columns": [], "rows": [], "truncated": False}
                if not expected_files else
                files_mod.preview_csv(Path(expected_files[0]["path"]).read_bytes()))
    produced_path = attempt["code_path"]  # stub stores the produced.csv here
    produced = ({"columns": [], "rows": [], "truncated": False}
                if not produced_path or not Path(produced_path).exists() else
                files_mod.preview_csv(Path(produced_path).read_bytes()))
    ncols = max(len(expected["columns"]), 1)
    wrong = [[i // ncols, i % ncols]
             for i, ch in enumerate(attempt["strip"] or "") if ch == "0"]
    return {"expected": expected, "produced": produced, "wrong_cells": wrong}


@app.get("/api/jobs/{job_id}/artifact")
async def artifact(job_id: str, user: dict = Depends(current_user)):
    get_job_or_404(job_id)
    tool = files_mod.job_dir(job_id) / "artifact" / "tool.py"
    if not tool.exists():
        raise HTTPException(404, "no artifact yet — train first")
    return FileResponse(tool, media_type="text/x-python", filename="tool.py")


@app.get("/api/jobs/{job_id}/guard")
async def guard(job_id: str, user: dict = Depends(current_user)):
    get_job_or_404(job_id)
    report = engine_stub.guard_report(job_id)
    return GuardReport(**report).model_dump(by_alias=True)


# ── the trained intern ─────────────────────────────────────────────────

@app.post("/api/i/{slug}/run")
async def run_intern(slug: str, file: list[UploadFile] = File(...)):
    job = store.get_job_by_slug(slug)
    if not job:
        raise HTTPException(404, "no intern at this address")
    if job["status"] != "ready":
        raise HTTPException(409, f"this intern isn't trained yet (status: {job['status']})")
    if len(file) != 2:
        raise HTTPException(400, "send exactly two files: the manifest and the rate card")
    run_id = store.new_id()
    run_dir = files_mod.job_dir(job["id"]) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    input_paths = []
    for up in file:
        dest = run_dir / files_mod.safe_filename(up.filename or "input.csv")
        dest.write_bytes(await up.read())
        input_paths.append(str(dest))
    result = engine_stub.run_artifact(job["id"], input_paths, run_dir)
    store.add_run(job["id"], result["ms"], result["ok"])
    if not result["ok"]:
        raise HTTPException(500, f"the intern hit an error: {result['stderr'][-500:]}")
    preview = files_mod.preview_csv(Path(result["out_path"]).read_bytes())
    return {"download_url": f"/api/i/{slug}/runs/{run_id}/download",
            "preview": preview, "ms": result["ms"]}


@app.get("/api/i/{slug}/runs/{run_id}/download")
async def download_run(slug: str, run_id: str):
    job = store.get_job_by_slug(slug)
    if not job:
        raise HTTPException(404, "no intern at this address")
    out = files_mod.job_dir(job["id"]) / "runs" / files_mod.safe_filename(run_id) / "summary.csv"
    if not out.exists():
        raise HTTPException(404, "no output for this run")
    return FileResponse(out, media_type="text/csv", filename="summary.csv")


@app.get("/api/health")
async def health():
    return {"ok": True}
