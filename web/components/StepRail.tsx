"use client";

import React from "react";
import Link from "next/link";

const STEPS = [
  { n: 1, label: "The brief", seg: "new" },
  { n: 2, label: "Questions", seg: "questions" },
  { n: 3, label: "Read-back", seg: "readback" },
  { n: 4, label: "Show me one", seg: "example" },
  { n: 5, label: "Training", seg: "training" },
  { n: 6, label: "First day", seg: "ready" },
];

function hrefFor(seg: string, jobId?: string): string {
  if (seg === "new") return "/train/new";
  return jobId ? `/train/${jobId}/${seg}` : "/train/new";
}

function Dot({ state }: { state: "done" | "current" | "todo" }) {
  if (state === "done")
    return (
      <span
        aria-hidden="true"
        style={{
          width: 10,
          height: 10,
          borderRadius: "var(--r-full)",
          background: "var(--ink-900)",
          flex: "none",
        }}
      />
    );
  if (state === "current")
    return (
      <span
        aria-hidden="true"
        style={{
          width: 10,
          height: 10,
          borderRadius: "var(--r-full)",
          border: "2px solid var(--ink-900)",
          background: "var(--paper-0)",
          flex: "none",
        }}
      />
    );
  return (
    <span
      aria-hidden="true"
      style={{
        width: 10,
        height: 10,
        borderRadius: "var(--r-full)",
        border: "1px solid var(--ink-300)",
        background: "var(--paper-0)",
        flex: "none",
      }}
    />
  );
}

/** Fixed left column on desktop, horizontal bar on mobile.
 *  Steps before the current one are clickable — the emergency exit. */
export function StepRail({ current, jobId }: { current: number; jobId?: string }) {
  return (
    <nav aria-label="Steps" className="steprail">
      <ol className="steprail-list" style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {STEPS.map((s, i) => {
          const state = s.n < current ? "done" : s.n === current ? "current" : "todo";
          const clickable = s.n < current;
          const inner = (
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--s-2)",
                minHeight: 28,
              }}
            >
              <Dot state={state} />
              <span
                className={state === "done" || state === "current" ? "body-strong" : "body-text"}
                style={{
                  color:
                    state === "todo"
                      ? "var(--ink-300)"
                      : state === "current"
                        ? "var(--ink-900)"
                        : "var(--ink-700)",
                  borderLeft: state === "current" ? "var(--rule-heavy)" : "2px solid transparent",
                  paddingLeft: "var(--s-2)",
                  fontSize: 14,
                  lineHeight: "20px",
                }}
              >
                <span className="data" style={{ fontSize: 12, marginRight: 6 }}>
                  {s.n}
                </span>
                {s.label}
              </span>
            </span>
          );
          return (
            <li key={s.n} className="steprail-item">
              {clickable ? (
                <Link
                  href={hrefFor(s.seg, jobId)}
                  style={{ textDecoration: "none", display: "block", borderRadius: "var(--r-1)" }}
                >
                  {inner}
                </Link>
              ) : (
                inner
              )}
              {i < STEPS.length - 1 && (
                <span
                  aria-hidden="true"
                  className="steprail-line"
                  style={{
                    display: "block",
                    width: 1,
                    height: 16,
                    marginLeft: 4.5,
                    background: s.n < current ? "var(--ink-900)" : "var(--ink-100)",
                  }}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
