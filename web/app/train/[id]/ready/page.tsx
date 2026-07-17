"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { StepShell } from "@/components/StepShell";
import { Sheet } from "@/components/Sheet";
import { Button } from "@/components/Button";
import { Well } from "@/components/Well";
import { apiGet, isMockJob } from "@/lib/api";
import { MOCK_ARTIFACT, MOCK_GUARD, MOCK_SLUG } from "@/lib/mockData";
import { downloadText } from "@/lib/csv";
import type { GuardReport, Job } from "@/lib/types";

function timeOf(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

export default function ReadyPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params.id;

  const [job, setJob] = useState<Job | null>(null);
  const [guard, setGuard] = useState<GuardReport | null>(null);
  const [code, setCode] = useState<string>(MOCK_ARTIFACT);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (isMockJob(jobId)) {
      setGuard(MOCK_GUARD);
      return;
    }
    apiGet<{ job: Job }>(`/api/jobs/${jobId}`)
      .then((d) => {
        if (!cancelled) setJob(d.job);
      })
      .catch(() => {});
    apiGet<GuardReport>(`/api/jobs/${jobId}/guard`)
      .then((g) => {
        if (!cancelled) setGuard(g);
      })
      .catch(() => {
        if (!cancelled) setGuard(MOCK_GUARD);
      });
    fetch(`/api/jobs/${jobId}/artifact`, { credentials: "include" })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(String(r.status)))))
      .then((t) => {
        if (!cancelled) setCode(t);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const slug = job?.slug ?? MOCK_SLUG;
  const tries = job?.attempts_used ?? 5;
  const secs = Math.round((job?.train_ms ?? 41300) / 1000);
  const address = `intern.works/i/${slug}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };

  return (
    <StepShell step={6} jobId={jobId}>
      <h1 className="display-2">Your intern is ready.</h1>
      <p className="body-text measure" style={{ color: "var(--ink-500)", marginTop: "var(--s-4)" }}>
        It learned the job in <span className="data">{tries}</span> tries and{" "}
        <span className="data">{secs}</span> seconds. From now on it takes about a second, and
        it costs you nothing to run.
      </p>

      <div style={{ marginTop: "var(--s-6)" }}>
        <Sheet elevation={2}>
          <div className="label" style={{ color: "var(--ink-500)", marginBottom: "var(--s-4)" }}>
            Its address
          </div>
          <div style={{ display: "flex", gap: 0, alignItems: "stretch" }}>
            <div
              className="data"
              style={{
                flex: "1 1 auto",
                minWidth: 0,
                fontSize: 17,
                display: "flex",
                alignItems: "center",
                padding: "0 var(--s-3)",
                height: 44,
                background: "var(--paper-2)",
                border: "var(--rule-thin)",
                borderRight: "none",
                borderRadius: "var(--r-1) 0 0 var(--r-1)",
                boxShadow: "var(--press-1)",
                color: "var(--ink-900)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {address}
            </div>
            <button
              type="button"
              onClick={copy}
              className="body-text"
              style={{
                height: 44,
                padding: "0 var(--s-4)",
                background: "var(--paper-1)",
                border: "var(--rule-thin)",
                borderRadius: "0 var(--r-1) var(--r-1) 0",
                color: "var(--ink-900)",
                cursor: "pointer",
                flex: "none",
              }}
            >
              {copied ? "copied" : "copy"}
            </button>
          </div>
          <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
            Bookmark it. Drop your two files, get your summary. Send it to your drivers if you
            like — it&apos;s yours.
          </p>
          <div style={{ marginTop: "var(--s-4)" }}>
            <Button onClick={() => router.push(`/i/${slug}`)}>Open it now</Button>
          </div>
        </Sheet>
      </div>

      <div style={{ borderTop: "var(--rule-hair)", margin: "var(--s-6) 0" }} />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--s-3)",
        }}
      >
        <div className="label" style={{ color: "var(--ink-500)" }}>
          What it learned
        </div>
        <Button
          variant="quiet"
          onClick={() => {
            if (isMockJob(jobId)) downloadText("tool.py", code);
            else window.open(`/api/jobs/${jobId}/artifact`, "_blank");
          }}
        >
          download ↓
        </Button>
      </div>
      <Well code={code} maxHeight={320} />

      <div style={{ marginTop: "var(--s-6)" }}>
        <Sheet>
          <div className="title-2">
            <span aria-hidden="true">{guard?.pass === false ? "✗" : "✓"}</span>{" "}
            {guard?.pass === false ? "The check did not pass" : "No AI inside"}
          </div>
          {guard?.pass === false ? (
            <p className="body-text" style={{ color: "var(--ink-700)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
              The check found something it shouldn&apos;t have:{" "}
              <span className="data">{guard.violations.join(", ")}</span>. Don&apos;t use this
              one — go back a step and train it again.
            </p>
          ) : (
            <p className="body-text" style={{ color: "var(--ink-700)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
              This program has no model in it, makes no calls to the internet, and can&apos;t
              invent anything. It does the same thing every time. We checked — that&apos;s why
              it&apos;s $20 once and not a meter.
            </p>
          )}
          {guard && (
            <p className="data" style={{ fontSize: 13, color: "var(--ink-500)", marginTop: "var(--s-3)" }}>
              network calls {guard.network_calls} · model calls {guard.model_calls} · checked at{" "}
              {timeOf(guard.checked_at)}
            </p>
          )}
        </Sheet>
      </div>
    </StepShell>
  );
}
