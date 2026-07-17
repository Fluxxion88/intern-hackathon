import type { LoopEvent } from "./types";
import rawEvents from "@/mocks/events.json";

export const MOCK_EVENTS = rawEvents as LoopEvent[];

/** Delay before each event, in ms, at speed = 1. */
function delayFor(ev: LoopEvent): number {
  switch (ev.type) {
    case "phase":
      return 650;
    case "attempt.started":
      return 250;
    case "attempt.scored":
      return 500;
    case "converged":
      return 900;
    default:
      return 200;
  }
}

/** Replays web/mocks/events.json into the same reducer the SSE feeds.
 *  Used by the landing hero auto-play and by the training screen when
 *  NEXT_PUBLIC_MOCK=1 or the API is unreachable. Returns a stop(). */
export function replayMockEvents(
  onEvent: (ev: LoopEvent) => void,
  opts: { speed?: number; loop?: boolean; loopPauseMs?: number; onCycleEnd?: () => void } = {}
): () => void {
  const { speed = 1, loop = false, loopPauseMs = 2200, onCycleEnd } = opts;
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const runFrom = (i: number) => {
    if (stopped) return;
    if (i >= MOCK_EVENTS.length) {
      onCycleEnd?.();
      if (loop) timer = setTimeout(() => runFrom(0), loopPauseMs);
      return;
    }
    const ev = MOCK_EVENTS[i];
    timer = setTimeout(() => {
      if (stopped) return;
      onEvent(ev);
      runFrom(i + 1);
    }, delayFor(ev) / speed);
  };

  runFrom(0);
  return () => {
    stopped = true;
    if (timer) clearTimeout(timer);
  };
}
