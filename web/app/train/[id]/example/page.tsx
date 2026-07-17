"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { StepShell } from "@/components/StepShell";
import { Button } from "@/components/Button";
import { DropZone } from "@/components/DropZone";
import { FileChip } from "@/components/FileChip";
import { Table } from "@/components/Table";
import { apiUpload, apiPost, isMockJob } from "@/lib/api";
import { parseCsv } from "@/lib/csv";
import type { FilePreview, UploadedFile } from "@/lib/types";

interface PickedFile {
  filename: string;
  bytes: number;
  preview: FilePreview;
  error?: string;
}

export default function ExamplePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params.id;

  const [inputs, setInputs] = useState<PickedFile[]>([]);
  const [expected, setExpected] = useState<PickedFile | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const readFile = async (file: File, role: "input" | "expected"): Promise<PickedFile> => {
    // Client-side receipt first — so he finds out now, not four minutes into training.
    const text = await file.text();
    const preview = parseCsv(text);
    const picked: PickedFile = { filename: file.name, bytes: file.size, preview };
    if (preview.columns.length < 2) {
      picked.error = `This one doesn't look like a table of columns. Save the sheet you use as a CSV and drop it again.`;
    }
    if (!isMockJob(jobId)) {
      try {
        const form = new FormData();
        form.append("role", role);
        form.append("file", file);
        const res = await apiUpload<{ file: UploadedFile; preview: FilePreview }>(
          `/api/jobs/${jobId}/files`,
          form
        );
        if (res.preview) picked.preview = res.preview;
      } catch {
        // Keep the client-side preview — the demo must not stall here.
      }
    }
    return picked;
  };

  const onInputFiles = async (files: File[]) => {
    setProblem(null);
    const picked = await Promise.all(files.slice(0, 2).map((f) => readFile(f, "input")));
    setInputs((prev) => [...prev, ...picked].slice(0, 2));
  };

  const onExpectedFiles = async (files: File[]) => {
    setProblem(null);
    const [picked] = await Promise.all(files.slice(0, 1).map((f) => readFile(f, "expected")));
    if (picked) setExpected(picked);
  };

  const ready = inputs.length === 2 && expected !== null && !expected.error;

  const start = async () => {
    setStarting(true);
    if (!isMockJob(jobId)) {
      try {
        await apiPost(`/api/jobs/${jobId}/train`, {});
        router.push(`/train/${jobId}/training`);
        return;
      } catch {
        setProblem(
          "I couldn't reach the desk just now. Give it a second and press the button again."
        );
        setStarting(false);
        return;
      }
    }
    router.push(`/train/${jobId}/training`);
  };

  return (
    <StepShell step={4} jobId={jobId}>
      <h1 className="display-2">Now show me one you did yourself.</h1>
      <p className="body-text measure" style={{ color: "var(--ink-500)", marginTop: "var(--s-4)" }}>
        Two you started with, and the one you finished. Last Tuesday&apos;s is fine. This is how
        I&apos;ll know I&apos;ve got it right — I&apos;ll practise until mine matches yours
        exactly.
      </p>

      <div className="label" style={{ color: "var(--ink-500)", marginTop: "var(--s-6)", marginBottom: "var(--s-3)" }}>
        What you started with
      </div>
      {inputs.length < 2 && (
        <DropZone
          title="Drop your two files here"
          subtitle="or click to choose"
          onFiles={onInputFiles}
        />
      )}
      {inputs.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--s-2)", marginTop: "var(--s-2)" }}>
          {inputs.map((f, i) => (
            <FileChip
              key={`${f.filename}-${i}`}
              filename={f.filename}
              bytes={f.bytes}
              ok={!f.error}
              onRemove={() => setInputs((prev) => prev.filter((_, j) => j !== i))}
            />
          ))}
        </div>
      )}

      <div className="label" style={{ color: "var(--ink-500)", marginTop: "var(--s-6)", marginBottom: "var(--s-3)" }}>
        What you finished
      </div>
      {!expected && (
        <DropZone
          title="Drop the summary you made from them"
          subtitle="or click to choose"
          onFiles={onExpectedFiles}
          multiple={false}
        />
      )}
      {expected && (
        <div style={{ marginTop: "var(--s-2)" }}>
          <FileChip
            filename={expected.filename}
            bytes={expected.bytes}
            ok={!expected.error}
            onRemove={() => setExpected(null)}
          />
          {expected.error && (
            <p className="body-strong" style={{ color: "var(--ink-900)", marginTop: "var(--s-2)" }}>
              ✗ {expected.error}
            </p>
          )}
        </div>
      )}

      {expected && !expected.error && (
        <>
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
              Here&apos;s what I can see
            </div>
            <Button variant="quiet" onClick={() => setShowAll((v) => !v)}>
              {showAll ? "show fewer rows ↑" : "show all rows ↓"}
            </Button>
          </div>
          <Table
            columns={expected.preview.columns}
            rows={expected.preview.rows}
            maxRows={showAll ? undefined : 5}
          />
        </>
      )}

      {problem && (
        <p className="body-strong" style={{ color: "var(--ink-900)", marginTop: "var(--s-4)" }}>
          ✗ {problem}
        </p>
      )}

      <div style={{ marginTop: "var(--s-6)" }}>
        <Button disabled={!ready || starting} onClick={start}>
          Start practising
        </Button>
      </div>
    </StepShell>
  );
}
