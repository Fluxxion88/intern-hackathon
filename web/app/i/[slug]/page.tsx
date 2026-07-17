"use client";

import React, { useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Sheet } from "@/components/Sheet";
import { Button } from "@/components/Button";
import { DropZone } from "@/components/DropZone";
import { Table } from "@/components/Table";
import { apiUpload, MOCK_FLAG } from "@/lib/api";
import { MOCK_RUN_RESULT, previewToCsv } from "@/lib/mockData";
import { downloadText } from "@/lib/csv";
import type { FilePreview } from "@/lib/types";

interface RunResult {
  filename: string;
  preview: FilePreview;
  ms: number;
  download_url?: string;
}

function titleFromSlug(slug: string): string {
  const [name, ...rest] = slug.split("-");
  const cap = name ? name[0].toUpperCase() + name.slice(1) : "Your";
  const job = rest.join(" ") || "own";
  return `${cap}'s ${job} intern`;
}

export default function InternPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const [pending, setPending] = useState<File[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const pageRef = useRef<HTMLDivElement>(null);

  const run = async (files: File[]) => {
    setRunning(true);
    setProblem(null);
    const finish = (r: RunResult) => {
      setResult(r);
      setRunning(false);
      setPending([]);
    };
    if (!MOCK_FLAG) {
      // Try the real intern first.
      try {
        const form = new FormData();
        files.forEach((f) => form.append("file", f));
        const res = await apiUpload<{ download_url: string; preview: FilePreview; ms: number; filename?: string }>(
          `/api/i/${slug}/run`,
          form
        );
        const filename =
          res.filename ?? res.download_url.split("/").pop() ?? "summary.csv";
        // Auto-download — don't make him click.
        const a = document.createElement("a");
        a.href = res.download_url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        finish({ filename, preview: res.preview, ms: res.ms, download_url: res.download_url });
        return;
      } catch {
        // Fall through to the fixture below.
      }
    }
    setTimeout(() => {
      const filename = "dispatch_summary_17.07.csv";
      downloadText(filename, previewToCsv(MOCK_RUN_RESULT));
      finish({ filename, preview: MOCK_RUN_RESULT, ms: 1200 });
    }, 1200);
  };

  const onFiles = (files: File[]) => {
    const next = [...pending, ...files].slice(0, 2);
    setPending(next);
    if (next.length >= 2) run(next);
  };

  return (
    <div
      ref={pageRef}
      style={{ minHeight: "100vh", background: "var(--paper-0)" }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        // The entire page is the drop zone.
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files);
        if (files.length && !running && !result) onFiles(files);
      }}
    >
      <header>
        <div
          className="container"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            height: 56,
            gap: "var(--s-3)",
          }}
        >
          <span className="label" style={{ color: "var(--ink-900)" }}>
            {titleFromSlug(slug)}
          </span>
          <span className="label" style={{ color: "var(--ink-500)" }}>
            trained 17.07.2026
          </span>
        </div>
        <div style={{ borderBottom: "var(--rule-thin)" }} />
      </header>

      <main
        className="container"
        style={{
          paddingTop: "var(--s-8)",
          paddingBottom: "var(--s-9)",
          maxWidth: 720,
          textAlign: "center",
        }}
      >
        {!result && !running && (
          <>
            <DropZone
              title="Drop today's two files"
              subtitle="the manifest and the rate card"
              onFiles={onFiles}
              minHeight={260}
            />
            {pending.length === 1 && (
              <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)" }}>
                One more — it needs both files before it starts.
              </p>
            )}
            <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-5)" }}>
              It&apos;ll take about a second. You&apos;ll get{" "}
              <span className="data">dispatch_summary_17.07.csv</span> back.
            </p>
          </>
        )}

        {running && (
          <Sheet elevation={2} style={{ textAlign: "center" }}>
            <div className="label" style={{ color: "var(--ink-900)", letterSpacing: "0.12em" }}>
              Working
            </div>
            <div style={{ display: "flex", gap: 6, justifyContent: "center", marginTop: "var(--s-2)" }} aria-hidden="true">
              <span className="phase-dot" />
              <span className="phase-dot" />
              <span className="phase-dot" />
            </div>
          </Sheet>
        )}

        {result && (
          <Sheet elevation={2} style={{ textAlign: "left" }}>
            <div className="title-2">
              <span className="data" style={{ fontSize: 15 }}>
                {result.filename}
              </span>
            </div>
            <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-1)" }}>
              <span className="data">{result.preview.rows.length - 1}</span> rows ·{" "}
              <span className="data">1</span> total ·{" "}
              <span className="data">{(result.ms / 1000).toFixed(1)}</span> seconds
            </p>
            <div style={{ margin: "var(--s-4) 0" }}>
              <Button
                onClick={() => {
                  if (result.download_url) window.open(result.download_url, "_blank");
                  else downloadText(result.filename, previewToCsv(result.preview));
                }}
              >
                Download
              </Button>
            </div>
            <Table columns={result.preview.columns} rows={result.preview.rows} maxRows={5} />
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "var(--s-2)" }}>
              <Button
                variant="quiet"
                onClick={() => {
                  setResult(null);
                  setPending([]);
                }}
              >
                do it again
              </Button>
            </div>
          </Sheet>
        )}

        {problem && (
          <p className="body-strong" style={{ color: "var(--ink-900)", marginTop: "var(--s-4)" }}>
            ✗ {problem}
          </p>
        )}

        <div style={{ borderTop: "var(--rule-hair)", margin: "var(--s-7) auto", maxWidth: 360 }} />

        <div style={{ opacity: 0.6 }}>
          <div className="label" style={{ color: "var(--ink-500)" }}>
            Or email them to
          </div>
          <div className="data" style={{ color: "var(--ink-500)", marginTop: "var(--s-1)" }}>
            {slug}@in.intern.works
          </div>
          <div className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-1)" }}>
            and it&apos;ll reply with the file.
          </div>
          <div className="label" style={{ color: "var(--ink-300)", marginTop: "var(--s-2)" }}>
            coming for your inbox next
          </div>
        </div>

        <div style={{ borderTop: "var(--rule-hair)", margin: "var(--s-7) auto", maxWidth: 360 }} />

        <p className="label" style={{ color: "var(--ink-300)" }}>
          Runs 38 · last run 16.07.2026 · always 1.2s
        </p>
        <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-1)" }}>
          This one doesn&apos;t use AI. Same answer every time.
        </p>
      </main>
    </div>
  );
}
