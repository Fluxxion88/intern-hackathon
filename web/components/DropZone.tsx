"use client";

import React, { useRef, useState } from "react";

/** The only dashed border in the product: a space waiting to be filled. */
export function DropZone({
  title,
  subtitle,
  onFiles,
  minHeight = 180,
  multiple = true,
}: {
  title: string;
  subtitle?: string;
  onFiles: (files: File[]) => void;
  minHeight?: number;
  multiple?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={title}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const files = Array.from(e.dataTransfer.files);
        if (files.length) onFiles(files);
      }}
      style={{
        border: over ? "2px dashed var(--ink-900)" : "1px dashed var(--ink-100)",
        borderRadius: "var(--r-0)",
        background: over ? "var(--paper-1)" : "var(--paper-2)",
        boxShadow: "var(--press-1)",
        minHeight,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--s-2)",
        cursor: "pointer",
        padding: "var(--s-5)",
        textAlign: "center",
      }}
    >
      <span aria-hidden="true" style={{ color: "var(--ink-500)", fontSize: 17 }}>
        ↓
      </span>
      <div className="title-2">{title}</div>
      {subtitle && (
        <div className="body-text" style={{ color: "var(--ink-500)" }}>
          {subtitle}
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept=".csv,text/csv"
        style={{ display: "none" }}
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          if (files.length) onFiles(files);
          e.target.value = "";
        }}
      />
    </div>
  );
}
