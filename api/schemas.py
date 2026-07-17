"""SHARED CONTRACT — mirrored by hand in web/lib/types.ts. Change both or neither."""
from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

JobStatus = Literal["draft", "questioning", "readback", "example", "training", "ready", "failed"]
Outcome = Literal["PERFECT", "PLATEAU", "BUDGET", "FAILED"]
Phase = Literal["WRITING", "RUNNING", "CHECKING", "FIXING"]


class Question(BaseModel):
    id: str
    question: str
    why: str                      # always present — the "why" under each question
    suggestions: list[str] = []   # 0-3 tappable answers
    answer: Optional[str] = None


class SpecRule(BaseModel):
    n: int
    text: str                     # Andrei-language, his words
    confidence: float             # 0-1
    source: Literal["said", "asked", "guessed"]


class JobSpec(BaseModel):
    rules: list[SpecRule]
    guesses: list[str]            # >=2 always, even when confident
    output_columns: list[str]
    slug: str


class Attempt(BaseModel):
    n: int
    score: float                  # 0-1
    cells_ok: int
    cells_total: int
    strip: str                    # "1101…" one char per expected cell, row-major
    headline: str                 # plain language, lands on a LedgerSlip
    changed: str                  # "rounding on the Cost column"
    duration_ms: int
    at: str                       # ISO


class PhaseEvent(BaseModel):
    type: Literal["phase"] = "phase"
    phase: Phase


class AttemptStartedEvent(BaseModel):
    type: Literal["attempt.started"] = "attempt.started"
    n: int


class AttemptScoredEvent(BaseModel):
    type: Literal["attempt.scored"] = "attempt.scored"
    attempt: Attempt


class ConvergedEvent(BaseModel):
    type: Literal["converged"] = "converged"
    outcome: Outcome
    best: float
    attempts: int
    ms: int


class FailedEvent(BaseModel):
    type: Literal["failed"] = "failed"
    reason: str
    hint: str


class LogEvent(BaseModel):
    type: Literal["log"] = "log"
    line: str


LoopEvent = Union[PhaseEvent, AttemptStartedEvent, AttemptScoredEvent,
                  ConvergedEvent, FailedEvent, LogEvent]


class FilePreview(BaseModel):
    columns: list[str]
    rows: list[list[str]]
    truncated: bool


class UploadedFile(BaseModel):
    id: str
    role: Literal["input", "expected", "today"]
    filename: str
    bytes: int
    preview: FilePreview


class GuardReport(BaseModel):
    pass_: bool = Field(alias="pass")
    network_calls: int
    model_calls: int
    checked_at: str
    violations: list[str] = []

    model_config = {"populate_by_name": True}


class Job(BaseModel):
    id: str
    slug: Optional[str] = None
    brief: str
    status: JobStatus
    outcome: Optional[Outcome] = None
    best_score: Optional[float] = None
    attempts_used: Optional[int] = None
    train_ms: Optional[int] = None
    created_at: str
