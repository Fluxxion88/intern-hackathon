"use client";

import React, { useEffect, useRef, useState } from "react";
import { LedgerSlip } from "./LedgerSlip";
import { Stamp } from "./Stamp";
import { initialTrainState, reduceTrain, TrainState, rebuildFromAttempts } from "@/lib/reducer";
import { replayMockEvents, MOCK_EVENTS } from "@/lib/mockDriver";
import type { LoopEvent } from "@/lib/types";

/** The landing hero IS the Ledger, auto-playing on a loop: slips landing
 *  one after another, then the stamp. Nothing else on the page moves. */
export function HeroLedger() {
  const [state, setState] = useState<TrainState>(initialTrainState);
  const wasDoneRef = useRef(false);

  useEffect(() => {
    // prefers-reduced-motion: show the final state, no landing animation.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      let final = rebuildFromAttempts(
        MOCK_EVENTS.filter((e) => e.type === "attempt.scored").map(
          (e) => (e as Extract<LoopEvent, { type: "attempt.scored" }>).attempt
        )
      );
      const conv = MOCK_EVENTS.find((e) => e.type === "converged");
      if (conv) final = reduceTrain(final, conv);
      setState(final);
      return;
    }
    const stop = replayMockEvents(
      (ev) => {
        setState((s) => {
          // A fresh cycle begins after a converged run: reset the desk.
          const base = wasDoneRef.current ? initialTrainState : s;
          if (wasDoneRef.current) wasDoneRef.current = false;
          const next = reduceTrain(base, ev);
          if (next.done) wasDoneRef.current = true;
          return next;
        });
      },
      { speed: 1.6, loop: true, loopPauseMs: 2600 }
    );
    return () => stop();
  }, []);

  const slips = [...state.attempts].reverse().slice(0, 3);
  const newestN = state.attempts.length ? state.attempts[state.attempts.length - 1].n : null;
  const converged = state.converged;

  return (
    <div
      aria-label="Watch the intern practise: five attempts, then the stamp"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--s-3)",
        position: "relative",
        minHeight: 420,
      }}
    >
      {slips.map((a) => (
        <div key={a.n} style={{ position: "relative" }}>
          <LedgerSlip
            attempt={a}
            current={a.n === newestN}
            animate={a.n === newestN && !converged}
            recoil={a.n === newestN && converged?.outcome === "PERFECT"}
            showTime={false}
          >
            {a.n === newestN && converged?.outcome === "PERFECT" && (
              <div
                style={{
                  position: "absolute",
                  right: "var(--s-9)",
                  bottom: -28,
                  zIndex: 5,
                  pointerEvents: "none",
                }}
              >
                <Stamp
                  detail={`${Math.round(converged.best * 100)}% · ${converged.attempts} TRIES`}
                />
              </div>
            )}
          </LedgerSlip>
        </div>
      ))}
      {slips.length === 0 && (
        <div
          style={{
            border: "var(--rule-thin)",
            borderRadius: "var(--r-2)",
            background: "var(--paper-1)",
            boxShadow: "var(--lift-1)",
            padding: "var(--s-5)",
            minHeight: 120,
            display: "flex",
            alignItems: "center",
            gap: "var(--s-3)",
          }}
        >
          <span className="label" style={{ color: "var(--ink-500)", letterSpacing: "0.12em" }}>
            {state.phase ?? "WRITING"}
          </span>
          <span style={{ display: "flex", gap: 6 }} aria-hidden="true">
            <span className="phase-dot" />
            <span className="phase-dot" />
            <span className="phase-dot" />
          </span>
        </div>
      )}
    </div>
  );
}
