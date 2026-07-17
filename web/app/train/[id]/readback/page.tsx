"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { StepShell } from "@/components/StepShell";
import { Sheet } from "@/components/Sheet";
import { Button } from "@/components/Button";
import { apiGet, apiPatch, isMockJob } from "@/lib/api";
import { MOCK_SPEC } from "@/lib/mockData";
import type { JobSpec, SpecRule } from "@/lib/types";

export default function ReadbackPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params.id;

  const [spec, setSpec] = useState<JobSpec | null>(null);
  const [editing, setEditing] = useState(false);
  const [editingRule, setEditingRule] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [changed, setChanged] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    if (isMockJob(jobId)) {
      setSpec(MOCK_SPEC);
      return;
    }
    apiGet<{ spec: JobSpec | null }>(`/api/jobs/${jobId}`)
      .then((d) => {
        if (!cancelled) setSpec(d.spec ?? MOCK_SPEC);
      })
      .catch(() => {
        if (!cancelled) setSpec(MOCK_SPEC);
      });
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const saveRule = async (n: number) => {
    if (!spec) return;
    const rules: SpecRule[] = spec.rules.map((r) =>
      r.n === n ? { ...r, text: draft, source: "said" as const } : r
    );
    const next = { ...spec, rules };
    setSpec(next);
    setChanged((prev) => new Set(prev).add(n));
    setEditingRule(null);
    if (!isMockJob(jobId)) {
      try {
        const res = await apiPatch<{ spec: JobSpec }>(`/api/jobs/${jobId}/spec`, { rules });
        if (res.spec) setSpec(res.spec);
      } catch {
        // Keep the local edit — it re-sends when he approves.
      }
    }
  };

  return (
    <StepShell step={3} jobId={jobId}>
      <h1 className="display-2">Here&apos;s the job as I understand it.</h1>
      <p className="body-text measure" style={{ color: "var(--ink-500)", marginTop: "var(--s-4)" }}>
        Read it like you&apos;d read a new hire&apos;s notes. If anything is wrong, say so —
        it&apos;s much cheaper to fix now.
      </p>

      <div style={{ marginTop: "var(--s-6)" }}>
        <Sheet style={{ padding: "var(--s-6)" }}>
          <div className="label" style={{ color: "var(--ink-500)", marginBottom: "var(--s-4)" }}>
            Every morning I will
          </div>

          <ol style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {spec?.rules.map((rule) => (
              <li
                key={rule.n}
                className="readback-rule"
                style={{
                  display: "flex",
                  gap: "var(--s-3)",
                  padding: "var(--s-2) 0",
                  marginBottom: "var(--s-2)",
                  borderLeft: changed.has(rule.n) ? "var(--rule-heavy)" : "2px solid transparent",
                  paddingLeft: "var(--s-3)",
                }}
              >
                <span
                  className="data"
                  style={{ color: "var(--ink-500)", minWidth: 16, flex: "none", paddingTop: 2 }}
                >
                  {rule.n}
                </span>
                {editingRule === rule.n ? (
                  <div style={{ flex: "1 1 auto", minWidth: 0 }}>
                    <input
                      autoFocus
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveRule(rule.n);
                        if (e.key === "Escape") setEditingRule(null);
                      }}
                      className="body-text"
                      aria-label={`Rule ${rule.n}`}
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
                    <div style={{ display: "flex", gap: "var(--s-2)", marginTop: "var(--s-2)" }}>
                      <Button variant="quiet" onClick={() => saveRule(rule.n)}>
                        save
                      </Button>
                      <Button variant="quiet" onClick={() => setEditingRule(null)}>
                        cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <span
                      className="body-text"
                      style={{ color: "var(--ink-700)", flex: "1 1 auto", maxWidth: "62ch" }}
                    >
                      {rule.text}
                    </span>
                    {editing && (
                      <Button
                        variant="quiet"
                        onClick={() => {
                          setEditingRule(rule.n);
                          setDraft(rule.text);
                        }}
                      >
                        edit
                      </Button>
                    )}
                  </>
                )}
              </li>
            ))}
          </ol>

          <div style={{ borderTop: "var(--rule-hair)", margin: "var(--s-5) 0" }} />

          <div className="label" style={{ color: "var(--ink-500)", marginBottom: "var(--s-3)" }}>
            I&apos;m guessing on two things
          </div>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {spec?.guesses.map((g, i) => (
              <li
                key={i}
                className="body-text"
                style={{
                  color: "var(--ink-700)",
                  display: "flex",
                  gap: "var(--s-3)",
                  marginBottom: "var(--s-2)",
                  maxWidth: "62ch",
                }}
              >
                <span aria-hidden="true" style={{ color: "var(--ink-500)" }}>
                  ·
                </span>
                {g}
              </li>
            ))}
          </ul>
          <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
            Your example will settle both. If I&apos;m wrong you&apos;ll see it in the practice.
          </p>
        </Sheet>
      </div>

      <div style={{ display: "flex", gap: "var(--s-3)", marginTop: "var(--s-6)", flexWrap: "wrap" }}>
        <Button onClick={() => router.push(`/train/${jobId}/example`)}>
          That&apos;s the job
        </Button>
        <Button variant="secondary" onClick={() => setEditing((v) => !v)}>
          {editing ? "Done changing things" : "Something's wrong"}
        </Button>
      </div>
    </StepShell>
  );
}
