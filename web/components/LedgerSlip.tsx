"use client";

import React from "react";
import type { Attempt } from "@/lib/types";
import { CellStrip } from "./CellStrip";
import { Button } from "./Button";

function timeOf(iso: string): string {
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    const p = (n: number) => String(n).padStart(2, "0");
    return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
  } catch {
    return "";
  }
}

/** One attempt of the loop. Newest at top of the Ledger. */
export function LedgerSlip({
  attempt,
  current = false,
  animate = false,
  recoil = false,
  onSeeDiff,
  showTime = true,
  children,
}: {
  attempt: Attempt;
  current?: boolean;
  animate?: boolean;
  recoil?: boolean;
  onSeeDiff?: (n: number) => void;
  showTime?: boolean;
  children?: React.ReactNode; // the Stamp overlays here
}) {
  const ink = current ? "var(--ink-700)" : "var(--ink-500)";
  const pct = Math.round(attempt.score * 100);
  const t = showTime ? timeOf(attempt.at) : "";
  return (
    <div
      className={`${animate ? "anim-slip" : ""} ${recoil ? "anim-recoil" : ""}`}
      style={{
        position: "relative",
        background: "var(--paper-1)",
        border: "var(--rule-thin)",
        borderRadius: "var(--r-2)",
        boxShadow: current ? "var(--lift-2)" : "var(--lift-1)",
        padding: "var(--s-4) var(--s-5)",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: "var(--s-3)" }}>
        <div
          className="data"
          aria-hidden="true"
          style={{
            width: 28,
            height: 28,
            flex: "none",
            borderRadius: "var(--r-full)",
            border: "var(--rule-thin)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 13,
            color: current ? "var(--ink-900)" : "var(--ink-500)",
          }}
        >
          {attempt.n}
        </div>
        <div
          className="label"
          style={{ color: ink, paddingTop: 6, minWidth: 0, flex: "1 1 auto" }}
        >
          Attempt {attempt.n}
          {t ? ` · ${t}` : ""}
        </div>
        <div style={{ textAlign: "right", flex: "none" }}>
          <div className="data-lg" style={{ color: current ? "var(--ink-900)" : "var(--ink-500)" }}>
            {pct}%
          </div>
          <div className="label" style={{ color: "var(--ink-500)" }}>
            match
          </div>
        </div>
      </div>

      <div style={{ borderTop: "var(--rule-hair)", margin: "var(--s-3) 0" }} />

      <p className="body-text" style={{ color: ink, maxWidth: "62ch" }}>
        {attempt.headline}
      </p>

      <div style={{ marginTop: "var(--s-3)" }}>
        <CellStrip strip={attempt.strip} okCount={attempt.cells_ok} total={attempt.cells_total} />
      </div>

      {(attempt.changed || onSeeDiff) && (
        <div
          style={{
            marginTop: "var(--s-3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "var(--s-3)",
            flexWrap: "wrap",
          }}
        >
          <span className="label" style={{ color: "var(--ink-500)" }}>
            {attempt.changed ? `Changed: ${attempt.changed}` : ""}
          </span>
          {onSeeDiff && (
            <Button variant="quiet" onClick={() => onSeeDiff(attempt.n)}>
              [ see the diff ]
            </Button>
          )}
        </div>
      )}

      {children}
    </div>
  );
}
