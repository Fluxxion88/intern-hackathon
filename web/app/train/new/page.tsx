"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { StepShell } from "@/components/StepShell";
import { Button } from "@/components/Button";
import { apiPost, MOCK_FLAG } from "@/lib/api";
import { FREIGHT_BRIEF, MOCK_JOB_ID } from "@/lib/mockData";
import type { Question } from "@/lib/types";

export default function BriefPage() {
  const router = useRouter();
  const [brief, setBrief] = useState("");
  const [sending, setSending] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const send = async () => {
    if (!brief.trim()) {
      setProblem("Tell it the job first — even a couple of sentences is plenty.");
      return;
    }
    setProblem(null);
    setSending(true);
    if (!MOCK_FLAG) {
      try {
        const res = await apiPost<{ job_id: string; questions: Question[] }>(`/api/jobs`, {
          brief,
        });
        router.push(`/train/${res.job_id}/questions`);
        return;
      } catch {
        // API unreachable — carry on from fixtures. The demo never stalls.
      }
    }
    try {
      sessionStorage.setItem("intern.brief", brief);
    } catch {}
    router.push(`/train/${MOCK_JOB_ID}/questions`);
  };

  return (
    <StepShell step={1}>
      <h1 className="display-2">Tell your intern what the job is.</h1>
      <p className="body-text measure" style={{ color: "var(--ink-500)", marginTop: "var(--s-4)" }}>
        Explain it the way you&apos;d explain it to someone starting on Monday. Where the files
        come from, what you do to them, what the finished thing looks like. Don&apos;t tidy it
        up — it&apos;s better if you ramble.
      </p>

      <div style={{ marginTop: "var(--s-6)" }}>
        <label htmlFor="brief" className="label" style={{ color: "var(--ink-500)", display: "block", marginBottom: "var(--s-2)" }}>
          The job, in your words
        </label>
        <textarea
          id="brief"
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          className="body-text"
          placeholder="Every morning I get the manifest for the day and the rate card from accounts…"
          style={{
            width: "100%",
            minHeight: 260,
            padding: "var(--s-3)",
            background: "var(--paper-2)",
            border: "var(--rule-thin)",
            borderRadius: "var(--r-1)",
            boxShadow: "var(--press-1)",
            color: "var(--ink-900)",
            resize: "vertical",
            fontFamily: "var(--font-ui)",
          }}
        />
        <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-2)" }}>
          Say as much or as little as you like. It&apos;ll ask if it needs more.
        </p>
      </div>

      {problem && (
        <p className="body-strong" style={{ color: "var(--ink-900)", marginTop: "var(--s-3)" }}>
          ✗ {problem}
        </p>
      )}

      <div style={{ display: "flex", gap: "var(--s-3)", marginTop: "var(--s-6)", flexWrap: "wrap" }}>
        <Button onClick={send} disabled={sending}>
          Send it to your intern
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            setBrief(FREIGHT_BRIEF);
            setProblem(null);
          }}
          disabled={sending}
        >
          Use the freight example
        </Button>
      </div>
      {sending && (
        <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)" }}>
          It&apos;s reading your brief.
        </p>
      )}
    </StepShell>
  );
}
