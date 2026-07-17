"use client";

import React from "react";

function fmtBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  return `${Math.max(1, Math.round(b / 1024))} KB`;
}

/** ▤ is an inline SVG document glyph, not an emoji. Zero emoji in the product UI. */
function DocGlyph() {
  return (
    <svg
      width="12"
      height="14"
      viewBox="0 0 12 14"
      fill="none"
      aria-hidden="true"
      style={{ flex: "none" }}
    >
      <rect x="0.5" y="0.5" width="11" height="13" stroke="var(--ink-500)" />
      <line x1="2.5" y1="4" x2="9.5" y2="4" stroke="var(--ink-500)" />
      <line x1="2.5" y1="7" x2="9.5" y2="7" stroke="var(--ink-500)" />
      <line x1="2.5" y1="10" x2="9.5" y2="10" stroke="var(--ink-500)" />
    </svg>
  );
}

export function FileChip({
  filename,
  bytes,
  ok = true,
  onRemove,
}: {
  filename: string;
  bytes: number;
  ok?: boolean;
  onRemove?: () => void;
}) {
  return (
    <div
      className="data"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--s-3)",
        height: 36,
        padding: "0 var(--s-3)",
        border: "var(--rule-thin)",
        borderRadius: "var(--r-1)",
        background: "var(--paper-1)",
        color: "var(--ink-700)",
        minWidth: 0,
      }}
    >
      <DocGlyph />
      <span
        style={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          minWidth: 0,
          flex: "1 1 auto",
        }}
      >
        {filename}
      </span>
      <span style={{ color: "var(--ink-500)", flex: "none" }}>{fmtBytes(bytes)}</span>
      <span aria-hidden="true" style={{ color: ok ? "var(--ink-900)" : "var(--ink-300)", flex: "none" }}>
        ✓
      </span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${filename}`}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--ink-500)",
            cursor: "pointer",
            padding: "var(--s-1)",
            borderRadius: "var(--r-1)",
            fontFamily: "var(--font-data)",
            fontSize: 14,
            flex: "none",
          }}
        >
          ✕
        </button>
      )}
    </div>
  );
}
