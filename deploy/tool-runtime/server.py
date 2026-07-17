"""Tool runtime: one trained intern per container, same image for every intern.

Accepts two multipart files, runs the mounted /artifact/tool.py in a subprocess
with an EMPTY environment (no proxy vars, no creds — no network by policy; run
the container itself with --network=none for the hard guarantee), returns CSV.
Convention: python tool.py <input_a> <input_b> <out_csv> (per docs/04 §9).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, Response

ARTIFACT_DIR = Path(os.environ.get("ARTIFACT_DIR", "/artifact"))
TIMEOUT_S = int(os.environ.get("TOOL_TIMEOUT_S", "30"))

app = FastAPI(title="intern-tool-runtime")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "tool": os.environ.get("TOOL_SLUG", "unknown"),
            "artifact": (ARTIFACT_DIR / "tool.py").exists()}


@app.post("/run")
async def run(file_a: UploadFile = File(...), file_b: UploadFile = File(...)) -> Response:
    tool = ARTIFACT_DIR / "tool.py"
    if not tool.exists():
        raise HTTPException(503, "no artifact mounted at /artifact/tool.py")
    with tempfile.TemporaryDirectory() as td:
        a, b, out = Path(td) / "a.csv", Path(td) / "b.csv", Path(td) / "out.csv"
        a.write_bytes(await file_a.read())
        b.write_bytes(await file_b.read())
        try:
            proc = subprocess.run(
                [sys.executable, str(tool), str(a), str(b), str(out)],
                cwd=td, env={}, capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            raise HTTPException(504, f"tool exceeded {TIMEOUT_S}s")
        if proc.returncode != 0 or not out.exists():
            return PlainTextResponse(proc.stderr[-2000:] or "tool produced no output",
                                     status_code=422)
        return Response(out.read_bytes(), media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=summary.csv"})
