"use client";

import { useEffect, useRef, useState } from "react";
import type { Attempt, LoopEvent } from "./types";
import { initialTrainState, rebuildFromAttempts, reduceTrain, TrainState } from "./reducer";
import { replayMockEvents } from "./mockDriver";
import { isMockJob } from "./api";

export type TrainingMode = "connecting" | "live" | "mock";

/** Feeds the training reducer from the real SSE stream, or from the mock
 *  driver when NEXT_PUBLIC_MOCK=1, the job is the demo job, or the API is
 *  unreachable. Reconnects with exponential backoff; dedupes by attempt.n. */
export function useTraining(jobId: string): {
  state: TrainState;
  mode: TrainingMode;
  elapsedMs: number;
} {
  const [state, setState] = useState<TrainState>(initialTrainState);
  const [mode, setMode] = useState<TrainingMode>("connecting");
  const [elapsedMs, setElapsedMs] = useState(0);
  const doneRef = useRef(false);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    let es: EventSource | null = null;
    let stopMock: (() => void) | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let retries = 0;

    const dispatch = (ev: LoopEvent) => {
      if (cancelled) return;
      if (startRef.current === null) startRef.current = Date.now();
      setState((s) => {
        const next = reduceTrain(s, ev);
        doneRef.current = next.done;
        return next;
      });
    };

    const startMock = () => {
      if (cancelled || stopMock) return;
      setMode("mock");
      setState(initialTrainState);
      startRef.current = Date.now();
      stopMock = replayMockEvents(dispatch, { speed: 1 });
    };

    const connect = () => {
      if (cancelled || doneRef.current) return;
      es = new EventSource(`/api/jobs/${jobId}/events`, { withCredentials: true });
      es.onopen = () => {
        retries = 0;
        setMode("live");
      };
      es.onmessage = (m) => {
        try {
          const ev = JSON.parse(m.data) as LoopEvent | { type: "done" };
          if ((ev as { type: string }).type === "done") {
            es?.close();
            return;
          }
          dispatch(ev as LoopEvent);
        } catch {
          /* ignore malformed lines */
        }
      };
      es.onerror = () => {
        es?.close();
        es = null;
        if (cancelled || doneRef.current) return;
        retries += 1;
        if (retries > 4 && !stopMock) {
          // The API is unreachable — fall back to the fixture replay.
          startMock();
          return;
        }
        const backoff = Math.min(1000 * 2 ** (retries - 1), 15000);
        retryTimer = setTimeout(connect, backoff);
      };
    };

    if (isMockJob(jobId)) {
      startMock();
    } else {
      // Rebuild first — Andrei will refresh mid-training and the Ledger
      // must come back full.
      fetch(`/api/jobs/${jobId}`, { credentials: "include", cache: "no-store" })
        .then(async (res) => {
          if (!res.ok) throw new Error(String(res.status));
          const data = (await res.json()) as { attempts?: Attempt[] };
          if (cancelled) return;
          if (data.attempts?.length) {
            const rebuilt = rebuildFromAttempts(data.attempts);
            doneRef.current = rebuilt.done;
            setState(rebuilt);
          }
          connect();
        })
        .catch(() => {
          if (!cancelled) startMock();
        });
    }

    const tick = setInterval(() => {
      if (startRef.current !== null && !doneRef.current) {
        setElapsedMs(Date.now() - startRef.current);
      }
    }, 250);

    return () => {
      cancelled = true;
      es?.close();
      stopMock?.();
      if (retryTimer) clearTimeout(retryTimer);
      clearInterval(tick);
    };
  }, [jobId]);

  const finalMs = state.converged?.ms;
  return { state, mode, elapsedMs: finalMs ?? elapsedMs };
}
