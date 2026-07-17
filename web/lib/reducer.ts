import type { Attempt, LoopEvent, Outcome } from "./types";

export type Phase = "WRITING" | "RUNNING" | "CHECKING" | "FIXING";

export interface TrainState {
  attempts: Attempt[]; // ascending by n, deduped
  phase: Phase | null;
  bestScore: number; // never decreases
  bestCellsOk: number;
  cellsTotal: number;
  converged: { outcome: Outcome; best: number; attempts: number; ms: number } | null;
  failed: { reason: string; hint: string } | null;
  logs: string[];
  done: boolean;
}

export const initialTrainState: TrainState = {
  attempts: [],
  phase: null,
  bestScore: 0,
  bestCellsOk: 0,
  cellsTotal: 0,
  converged: null,
  failed: null,
  logs: [],
  done: false,
};

export function reduceTrain(state: TrainState, ev: LoopEvent): TrainState {
  switch (ev.type) {
    case "phase":
      return { ...state, phase: ev.phase };
    case "attempt.started":
      return state;
    case "attempt.scored": {
      // Dedupe by attempt.n — reconnects replay the backlog.
      if (state.attempts.some((a) => a.n === ev.attempt.n)) return state;
      const attempts = [...state.attempts, ev.attempt].sort((a, b) => a.n - b.n);
      const bestScore = Math.max(state.bestScore, ev.attempt.score);
      const bestCellsOk = Math.max(state.bestCellsOk, ev.attempt.cells_ok);
      return {
        ...state,
        attempts,
        bestScore,
        bestCellsOk,
        cellsTotal: ev.attempt.cells_total || state.cellsTotal,
      };
    }
    case "converged":
      return {
        ...state,
        phase: null,
        converged: { outcome: ev.outcome, best: ev.best, attempts: ev.attempts, ms: ev.ms },
        bestScore: Math.max(state.bestScore, ev.best),
        done: true,
      };
    case "failed":
      return { ...state, phase: null, failed: { reason: ev.reason, hint: ev.hint }, done: true };
    case "log":
      return { ...state, logs: [...state.logs, ev.line] };
    default:
      return state;
  }
}

/** Rebuild state from a GET /api/jobs/{id} payload — back/refresh never destroys work. */
export function rebuildFromAttempts(attempts: Attempt[]): TrainState {
  let s = initialTrainState;
  for (const a of attempts) {
    s = reduceTrain(s, { type: "attempt.scored", attempt: a });
  }
  return s;
}
