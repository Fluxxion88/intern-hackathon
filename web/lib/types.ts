// SHARED CONTRACT — mirrored by hand in api/schemas.py. Change both or neither.

export type JobStatus =
  | "draft" | "questioning" | "readback" | "example" | "training" | "ready" | "failed";

export type Outcome = "PERFECT" | "PLATEAU" | "BUDGET" | "FAILED";

export interface Question {
  id: string;
  question: string;      // "If a truck isn't on the rate card, what do I do with that run?"
  why: string;           // "I can't work out a cost without a rate…"  ← always present
  suggestions: string[]; // 0–3 tappable answers
  answer?: string;
}

export interface SpecRule {
  n: number;
  text: string;          // "Throw away any run under 500 kg."  ← Andrei-language
  confidence: number;    // 0–1
  source: "said" | "asked" | "guessed";   // drives the "I'm guessing" block
}

export interface JobSpec {
  rules: SpecRule[];
  guesses: string[];     // ≥2 always, even when confident
  output_columns: string[];
  slug: string;
}

export interface Attempt {
  n: number;
  score: number;         // 0–1
  cells_ok: number;
  cells_total: number;
  strip: string;         // "1101111011…" — 1 = cell matches, row-major
  headline: string;      // "Sorted the rows the way you asked. One cost is a dollar off."
  changed: string;       // "rounding on the Cost column"
  duration_ms: number;
  at: string;            // ISO
}

export type LoopEvent =
  | { type: "phase";           phase: "WRITING" | "RUNNING" | "CHECKING" | "FIXING" }
  | { type: "attempt.started"; n: number }
  | { type: "attempt.scored";  attempt: Attempt }
  | { type: "converged";       outcome: Outcome; best: number; attempts: number; ms: number }
  | { type: "failed";          reason: string; hint: string }
  | { type: "log";             line: string };   // dev only, never rendered to Andrei

export interface FilePreview {
  columns: string[];
  rows: string[][];
  truncated: boolean;
}

export interface UploadedFile {
  id: string;
  role: "input" | "expected" | "today";
  filename: string;
  bytes: number;
  preview: FilePreview;
}

export interface GuardReport {
  pass: boolean;
  network_calls: number;
  model_calls: number;
  checked_at: string;
  violations: string[];
}

export interface Job {
  id: string;
  slug: string | null;
  brief: string;
  status: JobStatus;
  outcome: Outcome | null;
  best_score: number | null;
  attempts_used: number | null;
  train_ms: number | null;
  created_at: string;
}
