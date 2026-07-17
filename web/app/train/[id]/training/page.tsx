"use client";

import React, { Suspense, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { StepShell } from "@/components/StepShell";
import { Sheet } from "@/components/Sheet";
import { Button } from "@/components/Button";
import { LedgerSlip } from "@/components/LedgerSlip";
import { Stamp } from "@/components/Stamp";
import { Table } from "@/components/Table";
import { Well } from "@/components/Well";
import { useTraining } from "@/lib/useTraining";
import { isMockJob } from "@/lib/api";
import { MOCK_ARTIFACT, MOCK_DIFF } from "@/lib/mockData";
import type { FilePreview } from "@/lib/types";

type DiffPayload = {
  expected: FilePreview;
  produced: FilePreview;
  wrong_cells: [number, number][];
};

function StatCell({
  value,
  label,
  live = false,
}: {
  value: React.ReactNode;
  label: React.ReactNode;
  live?: boolean;
}) {
  return (
    <div
      style={{
        background: "var(--paper-1)",
        border: "var(--rule-thin)",
        borderRadius: "var(--r-2)",
        boxShadow: "var(--lift-1)",
        padding: "var(--s-4)",
        textAlign: "center",
        minHeight: 92,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--s-1)",
      }}
      aria-live={live ? "polite" : undefined}
    >
      <div className="data-lg" style={{ color: "var(--ink-900)" }}>
        {value}
      </div>
      <div className="label" style={{ color: "var(--ink-500)" }}>
        {label}
      </div>
    </div>
  );
}

function PhaseCell({ phase }: { phase: string | null }) {
  return (
    <div
      style={{
        background: "var(--paper-1)",
        border: "var(--rule-thin)",
        borderRadius: "var(--r-2)",
        boxShadow: "var(--lift-1)",
        padding: "var(--s-4)",
        textAlign: "center",
        minHeight: 92,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--s-2)",
      }}
      aria-live="polite"
    >
      <div className="label" style={{ color: "var(--ink-900)", letterSpacing: "0.12em" }}>
        {phase ?? "DONE"}
      </div>
      {phase && (
        <div style={{ display: "flex", gap: 6 }} aria-hidden="true">
          <span className="phase-dot" />
          <span className="phase-dot" />
          <span className="phase-dot" />
        </div>
      )}
    </div>
  );
}

function DiffOverlay({
  jobId,
  attemptN,
  onClose,
}: {
  jobId: string;
  attemptN: number;
  onClose: () => void;
}) {
  const [diff, setDiff] = useState<DiffPayload | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fallback = () => {
      if (!cancelled) setDiff(MOCK_DIFF);
    };
    if (isMockJob(jobId)) {
      fallback();
    } else {
      fetch(`/api/jobs/${jobId}/attempts/${attemptN}/diff`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
        .then((d) => {
          if (!cancelled) setDiff(d as DiffPayload);
        })
        .catch(fallback);
    }
    return () => {
      cancelled = true;
    };
  }, [jobId, attemptN]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const wrongProduced = useMemo(
    () => new Set((diff?.wrong_cells ?? []).map(([r, c]) => `${r},${c}`)),
    [diff]
  );

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`The diff for attempt ${attemptN}`}
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(12,12,12,0.24)",
        zIndex: 50,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "var(--s-6) var(--s-4)",
        overflowY: "auto",
      }}
    >
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: 980 }}>
        <Sheet elevation={2}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "var(--s-4)",
            }}
          >
            <div className="title-2">
              Attempt <span className="data">{attemptN}</span> — yours against its try
            </div>
            <Button variant="quiet" onClick={onClose}>
              close
            </Button>
          </div>
          {diff ? (
            <div className="diff-grid">
              <div>
                <div className="label" style={{ color: "var(--ink-500)", marginBottom: "var(--s-2)" }}>
                  The one you made
                </div>
                <Table columns={diff.expected.columns} rows={diff.expected.rows} />
              </div>
              <div>
                <div className="label" style={{ color: "var(--ink-500)", marginBottom: "var(--s-2)" }}>
                  The one it made
                </div>
                <Table
                  columns={diff.produced.columns}
                  rows={diff.produced.rows}
                  wrongCells={wrongProduced}
                />
                <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)" }}>
                  The dark cells are the ones that don&apos;t match yours yet.
                </p>
              </div>
            </div>
          ) : (
            <p className="body-text" style={{ color: "var(--ink-500)" }}>
              Fetching the two files.
            </p>
          )}
        </Sheet>
      </div>
    </div>
  );
}

function ArtifactOverlay({ jobId, onClose }: { jobId: string; onClose: () => void }) {
  const [code, setCode] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fallback = () => {
      if (!cancelled) setCode(MOCK_ARTIFACT);
    };
    if (isMockJob(jobId)) {
      fallback();
    } else {
      fetch(`/api/jobs/${jobId}/artifact`, { credentials: "include" })
        .then((r) => (r.ok ? r.text() : Promise.reject(new Error(String(r.status)))))
        .then((t) => {
          if (!cancelled) setCode(t);
        })
        .catch(fallback);
    }
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="What it wrote"
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(12,12,12,0.24)",
        zIndex: 50,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "var(--s-6) var(--s-4)",
        overflowY: "auto",
      }}
    >
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: 720 }}>
        <Sheet elevation={2}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "var(--s-4)",
            }}
          >
            <div className="label" style={{ color: "var(--ink-500)" }}>
              What it learned
            </div>
            <Button variant="quiet" onClick={onClose}>
              close
            </Button>
          </div>
          {code ? (
            <Well code={code} maxHeight={420} />
          ) : (
            <p className="body-text" style={{ color: "var(--ink-500)" }}>
              Fetching it.
            </p>
          )}
        </Sheet>
      </div>
    </div>
  );
}

function TrainingInner() {
  const params = useParams<{ id: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const jobId = params.id;
  const dev = search.get("dev") === "1";

  const { state, elapsedMs } = useTraining(jobId);
  const [diffFor, setDiffFor] = useState<number | null>(null);
  const [showArtifact, setShowArtifact] = useState(false);

  const newest = state.attempts.length ? state.attempts[state.attempts.length - 1] : null;
  const slips = [...state.attempts].reverse(); // newest on top
  const pct = Math.round(state.bestScore * 100);
  const seconds = Math.max(0, Math.round(elapsedMs / 1000));
  const converged = state.converged;
  const perfect = converged?.outcome === "PERFECT";
  const partial = converged && (converged.outcome === "PLATEAU" || converged.outcome === "BUDGET");
  const missedCells = Math.max(0, state.cellsTotal - state.bestCellsOk);

  return (
    <StepShell step={5} jobId={jobId}>
      <h1 className="display-2">It&apos;s practising.</h1>
      <p
        className="body-text measure"
        style={{ color: "var(--ink-500)", marginTop: "var(--s-4)" }}
      >
        It writes a program, runs it on your two files, compares what came out against the one
        you made, and fixes what doesn&apos;t line up. You can watch, or come back in a minute.
      </p>

      <div className="stat-row" style={{ marginTop: "var(--s-6)" }}>
        <StatCell
          live
          value={converged ? converged.attempts : state.attempts.length}
          label={
            (converged ? converged.attempts : state.attempts.length) === 1 ? "try" : "tries"
          }
        />
        <StatCell live value={`${pct}%`} label="match" />
        <StatCell live value={seconds} label={seconds === 1 ? "second" : "seconds"} />
        <PhaseCell phase={converged || state.failed ? null : state.phase} />
      </div>

      <div style={{ borderTop: "var(--rule-hair)", margin: "var(--s-6) 0" }} />

      {state.failed && (
        <Sheet
          elevation={2}
          style={{ border: "var(--rule-heavy)", marginBottom: "var(--s-5)" }}
        >
          <p className="body-strong" style={{ color: "var(--ink-900)", maxWidth: "62ch" }}>
            {state.failed.reason}
          </p>
          {state.failed.hint && (
            <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
              {state.failed.hint}
            </p>
          )}
          <div style={{ marginTop: "var(--s-4)" }}>
            <Button variant="secondary" onClick={() => router.push(`/train/${jobId}/readback`)}>
              Back to the read-back
            </Button>
          </div>
        </Sheet>
      )}

      {partial && converged && (
        <Sheet
          elevation={2}
          style={{ border: "var(--rule-heavy)", marginBottom: "var(--s-5)" }}
        >
          <p className="title-2">
            It gets <span className="data-lg">{Math.round(converged.best * 100)}%</span> of this
            right on its own.
          </p>
          <p className="body-text" style={{ color: "var(--ink-700)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
            {missedCells > 0 ? (
              <>
                <span className="data">{missedCells}</span> cells it can&apos;t work out —
                they&apos;re marked <span className="data">CHECK</span> in the file so
                you&apos;ll spot them.{" "}
              </>
            ) : null}
            That&apos;s still most of your morning back. You can take it as it is, or add one
            more example you did and let it practise again.
          </p>
          <div style={{ display: "flex", gap: "var(--s-3)", marginTop: "var(--s-4)", flexWrap: "wrap" }}>
            <Button onClick={() => router.push(`/train/${jobId}/ready`)}>
              Take it at {Math.round(converged.best * 100)}%
            </Button>
            <Button variant="secondary" onClick={() => router.push(`/train/${jobId}/example`)}>
              Give it another example
            </Button>
          </div>
        </Sheet>
      )}

      <div
        style={{ display: "flex", flexDirection: "column", gap: "var(--s-4)" }}
        aria-live="polite"
      >
        {slips.map((a) => {
          const isNewest = newest !== null && a.n === newest.n;
          return (
            <div key={a.n} style={{ position: "relative" }}>
              <LedgerSlip
                attempt={a}
                current={isNewest}
                animate={isNewest && !converged}
                recoil={isNewest && perfect}
                onSeeDiff={(n) => setDiffFor(n)}
              >
                {isNewest && perfect && converged && (
                  <div
                    style={{
                      position: "absolute",
                      right: "var(--s-10)",
                      bottom: -30,
                      zIndex: 5,
                      pointerEvents: "none",
                    }}
                  >
                    <Stamp
                      detail={`${Math.round(converged.best * 100)}% · ${converged.attempts} ${
                        converged.attempts === 1 ? "TRY" : "TRIES"
                      }`}
                    />
                  </div>
                )}
              </LedgerSlip>
            </div>
          );
        })}
      </div>

      {converged && (
        <div
          style={{
            display: "flex",
            gap: "var(--s-3)",
            marginTop: "var(--s-8)",
            flexWrap: "wrap",
          }}
        >
          {perfect && (
            <Button onClick={() => router.push(`/train/${jobId}/ready`)}>
              It&apos;s ready — go
            </Button>
          )}
          <Button variant="secondary" onClick={() => setShowArtifact(true)}>
            Show me what it wrote
          </Button>
        </div>
      )}

      {dev && state.logs.length > 0 && (
        <div style={{ marginTop: "var(--s-6)" }}>
          <div className="label" style={{ color: "var(--ink-300)", marginBottom: "var(--s-2)" }}>
            Log
          </div>
          <div
            className="code"
            style={{
              background: "var(--paper-2)",
              boxShadow: "var(--press-1)",
              padding: "var(--s-3)",
              color: "var(--ink-500)",
              maxHeight: 200,
              overflow: "auto",
            }}
          >
            {state.logs.map((l, i) => (
              <div key={i}>{l}</div>
            ))}
          </div>
        </div>
      )}

      {diffFor !== null && (
        <DiffOverlay jobId={jobId} attemptN={diffFor} onClose={() => setDiffFor(null)} />
      )}
      {showArtifact && <ArtifactOverlay jobId={jobId} onClose={() => setShowArtifact(false)} />}
    </StepShell>
  );
}

export default function TrainingPage() {
  return (
    <Suspense fallback={null}>
      <TrainingInner />
    </Suspense>
  );
}
