"""engine/runner.py — sandboxed execution of model-written scripts.

Layers (docs/04 §7, cheapest first):
  1  subprocess, never exec/eval in-process
  2  cwd = fresh tempdir; only the input CSVs are copied in
  3  env = {} — nothing inherited, no keys, no AWS_*
  4  rlimits: CPU 10s, AS 512MB, FSIZE 32MB, NPROC (see note)
  5  20s wall clock, SIGKILL of the process group
  6  AST static check BEFORE running (network/subprocess/eval/exec/
     open-for-write outside the out dir are banned)
"""
from __future__ import annotations

import ast
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# NOTE on RLIMIT_NPROC: 0 breaks the child before exec on macOS (the limit is
# per-user, and the freshly-forked child already counts, so 0 kills any
# subsequent library call that probes process creation — and pandas' import
# machinery trips it). We set the limit in preexec_fn AFTER fork; a small
# positive value keeps fork bombs impossible while letting the interpreter
# and pandas import normally.
NPROC_LIMIT = 256 if sys.platform == "darwin" else 0

CPU_SECONDS = 10
AS_BYTES = 512 * 1024 * 1024
FSIZE_BYTES = 32 * 1024 * 1024
WALL_SECONDS = 20

BANNED_IMPORTS = {
    "socket", "requests", "urllib", "httpx", "aiohttp", "http",
    "subprocess", "multiprocessing", "ctypes",
    "anthropic", "openai", "boto3", "botocore", "litellm", "langchain",
}
BANNED_CALL_NAMES = {"eval", "exec", "compile", "__import__"}
BANNED_ATTR_CALLS = {("os", "system"), ("os", "popen"), ("os", "exec"),
                     ("os", "spawn"), ("os", "fork")}


@dataclass
class RunResult:
    ok: bool
    produced_path: Path | None
    stdout: str
    stderr: str
    duration_ms: int
    static_violations: list[str] = field(default_factory=list)
    timed_out: bool = False


def static_check(code: str) -> list[str]:
    """Layer 6: AST walk before the script is ever executed."""
    violations: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"syntax error: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                if root in BANNED_IMPORTS:
                    violations.append(f"banned import: {a.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in BANNED_IMPORTS:
                violations.append(f"banned import: from {node.module}")
        elif isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in BANNED_CALL_NAMES:
                violations.append(f"banned call: {fn.id}()")
            elif isinstance(fn, ast.Attribute):
                base = fn.value.id if isinstance(fn.value, ast.Name) else None
                for mod, name in BANNED_ATTR_CALLS:
                    if base == mod and fn.attr.startswith(name):
                        violations.append(f"banned call: {mod}.{fn.attr}()")
            # open(..., 'w') — writes must go through argv[3] only. We allow
            # open() calls whose mode is read; any explicit write mode is
            # flagged (pandas .to_csv covers the legitimate write path).
            if isinstance(fn, ast.Name) and fn.id == "open":
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                if isinstance(mode, str) and any(c in mode for c in "wax+"):
                    # writing is only legitimate to argv[3]; a constant path is not
                    if node.args and isinstance(node.args[0], ast.Constant):
                        violations.append("open() writing to a hard-coded path")
    return violations


def _preexec():
    """Runs in the child after fork, before exec. New pgid + rlimits."""
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (AS_BYTES, AS_BYTES))
    except (ValueError, OSError):
        pass  # macOS is picky about RLIMIT_AS; wall clock + CPU still bound us
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (FSIZE_BYTES, FSIZE_BYTES))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (NPROC_LIMIT, NPROC_LIMIT))
    except (ValueError, OSError):
        pass


def run(script_path: str | Path, inputs: list[str | Path],
        timeout: int = WALL_SECONDS) -> RunResult:
    code = Path(script_path).read_text()
    violations = static_check(code)
    if violations:
        return RunResult(False, None, "", "static check failed", 0,
                         static_violations=violations)

    workdir = Path(tempfile.mkdtemp(prefix="intern-run-"))
    try:
        local_inputs = []
        for p in inputs:
            dst = workdir / Path(p).name
            shutil.copy(Path(p), dst)
            local_inputs.append(dst)
        tool = workdir / "tool.py"
        tool.write_text(code)
        out = workdir / "out.csv"

        t0 = time.monotonic()
        proc = subprocess.Popen(
            [sys.executable, str(tool), *[str(p) for p in local_inputs], str(out)],
            cwd=str(workdir), env={},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=_preexec, text=True,
        )
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = proc.communicate()
        duration_ms = int((time.monotonic() - t0) * 1000)

        ok = proc.returncode == 0 and out.exists() and not timed_out
        if timed_out:
            stderr = (stderr or "") + f"\n[killed: exceeded {timeout}s wall clock]"
        elif proc.returncode == 0 and not out.exists():
            stderr = (stderr or "") + "\n[script exited 0 but wrote no output file]"

        produced = None
        if out.exists():
            # move the artifact out of the tempdir before cleanup
            keep = Path(tempfile.mkdtemp(prefix="intern-out-")) / "out.csv"
            shutil.move(str(out), keep)
            produced = keep
        return RunResult(ok, produced, stdout or "", stderr or "", duration_ms,
                         timed_out=timed_out)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
