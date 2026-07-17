import React from "react";
import Link from "next/link";
import { StepRail } from "./StepRail";

/** Header + rail + content grid shared by the six training steps. */
export function StepShell({
  step,
  jobId,
  children,
}: {
  step: number;
  jobId?: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ minHeight: "100vh", background: "var(--paper-0)" }}>
      <header>
        <div
          className="container"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            height: 56,
          }}
        >
          <Link
            href="/"
            className="label"
            style={{ color: "var(--ink-900)", textDecoration: "none", borderRadius: "var(--r-1)" }}
          >
            Intern
          </Link>
        </div>
        <div style={{ borderBottom: "var(--rule-thin)" }} />
      </header>
      <div className="container step-grid" style={{ paddingTop: "var(--s-7)", paddingBottom: "var(--s-9)" }}>
        <StepRail current={step} jobId={jobId} />
        <main className="step-content">{children}</main>
      </div>
    </div>
  );
}
