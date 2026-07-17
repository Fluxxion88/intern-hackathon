"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { StepShell } from "@/components/StepShell";
import { Sheet } from "@/components/Sheet";
import { Button } from "@/components/Button";
import { apiGet, apiPost, isMockJob } from "@/lib/api";
import { MOCK_QUESTIONS } from "@/lib/mockData";
import type { Question } from "@/lib/types";

export default function QuestionsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params.id;

  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [typed, setTyped] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (isMockJob(jobId)) {
      setQuestions(MOCK_QUESTIONS);
      return;
    }
    apiGet<{ job?: { questions?: Question[] }; questions?: Question[] }>(`/api/jobs/${jobId}`)
      .then((d) => {
        if (cancelled) return;
        const qs = d.questions ?? d.job?.questions ?? [];
        setQuestions(qs.length ? qs.slice(0, 3) : MOCK_QUESTIONS);
      })
      .catch(() => {
        if (!cancelled) setQuestions(MOCK_QUESTIONS);
      });
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const currentIdx = questions.findIndex((q) => answers[q.id] === undefined);
  const allAnswered = questions.length > 0 && currentIdx === -1;

  const finish = async (finalAnswers: Record<string, string>) => {
    setSending(true);
    if (!isMockJob(jobId)) {
      try {
        await apiPost(`/api/jobs/${jobId}/answers`, { answers: finalAnswers });
      } catch {
        // Fixture path continues regardless.
      }
    }
    router.push(`/train/${jobId}/readback`);
  };

  const answer = (q: Question, text: string) => {
    const next = { ...answers, [q.id]: text };
    setAnswers(next);
    setTyped("");
    if (questions.every((qq) => next[qq.id] !== undefined)) {
      finish(next);
    }
  };

  return (
    <StepShell step={2} jobId={jobId}>
      <h1 className="display-2">Three things I&apos;m not sure about.</h1>

      <div style={{ marginTop: "var(--s-6)", display: "flex", flexDirection: "column", gap: "var(--s-4)" }}>
        {questions.map((q, i) => {
          const done = answers[q.id] !== undefined;
          const isCurrent = i === currentIdx;

          if (done) {
            return (
              <div
                key={q.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--s-3)",
                  minHeight: 44,
                  padding: "var(--s-2) var(--s-4)",
                  border: "var(--rule-thin)",
                  borderRadius: "var(--r-2)",
                  background: "var(--paper-1)",
                  color: "var(--ink-500)",
                  flexWrap: "wrap",
                }}
              >
                <span aria-hidden="true" style={{ color: "var(--ink-900)" }}>
                  ✓
                </span>
                <span className="body-text" style={{ flex: "1 1 auto", minWidth: 0 }}>
                  {q.question} <span className="body-strong" style={{ color: "var(--ink-700)" }}>{answers[q.id]}</span>
                </span>
                <Button
                  variant="quiet"
                  onClick={() =>
                    setAnswers((prev) => {
                      const n = { ...prev };
                      delete n[q.id];
                      return n;
                    })
                  }
                >
                  edit
                </Button>
              </div>
            );
          }

          if (isCurrent) {
            return (
              <Sheet key={q.id} elevation={2} className="anim-slip">
                <div style={{ display: "flex", gap: "var(--s-3)" }}>
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
                    }}
                  >
                    {i + 1}
                  </div>
                  <div style={{ minWidth: 0, flex: "1 1 auto" }}>
                    <div className="title-2" style={{ maxWidth: "62ch" }}>
                      {q.question}
                    </div>
                    <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
                      {q.why}
                    </p>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "flex-start",
                        gap: "var(--s-2)",
                        marginTop: "var(--s-4)",
                      }}
                    >
                      {q.suggestions.map((s) => (
                        <Button key={s} variant="secondary" onClick={() => answer(q, s)}>
                          {s}
                        </Button>
                      ))}
                    </div>
                    <div style={{ marginTop: "var(--s-4)" }}>
                      <input
                        value={typed}
                        onChange={(e) => setTyped(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && typed.trim()) answer(q, typed.trim());
                        }}
                        placeholder="or tell me in your own words…"
                        aria-label="Answer in your own words"
                        className="body-text"
                        style={{
                          width: "100%",
                          height: 44,
                          padding: "0 var(--s-3)",
                          background: "var(--paper-2)",
                          border: "var(--rule-thin)",
                          borderRadius: "var(--r-1)",
                          boxShadow: "var(--press-1)",
                          color: "var(--ink-900)",
                        }}
                      />
                      <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-2)" }}>
                        Press Enter to answer.
                      </p>
                    </div>
                  </div>
                </div>
              </Sheet>
            );
          }

          return (
            <div
              key={q.id}
              className="data"
              style={{
                minHeight: 44,
                display: "flex",
                alignItems: "center",
                gap: "var(--s-3)",
                color: "var(--ink-300)",
                paddingLeft: "var(--s-2)",
              }}
            >
              <span aria-hidden="true" style={{ display: "flex", gap: 1 }}>
                {[0, 1, 2].map((k) => (
                  <span key={k} style={{ width: 3, height: 14, background: "var(--ink-100)" }} />
                ))}
              </span>
              {i + 1} · not asked yet
            </div>
          );
        })}
      </div>

      {allAnswered && sending && (
        <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-5)" }}>
          Writing the job down.
        </p>
      )}
    </StepShell>
  );
}
