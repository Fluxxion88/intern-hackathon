"use client";

import React from "react";

/** Text input. Help text is always present, never a tooltip.
 *  Error: heavy border, message says what to do — no red. */
export function Field({
  label,
  help,
  error,
  value,
  onChange,
  placeholder,
  type = "text",
  name,
  autoFocus,
  onKeyDown,
}: {
  label?: string;
  help?: string;
  error?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  name?: string;
  autoFocus?: boolean;
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}) {
  const id = React.useId();
  return (
    <div>
      {label && (
        <label
          htmlFor={id}
          className="label"
          style={{ color: "var(--ink-500)", display: "block", marginBottom: "var(--s-2)" }}
        >
          {label}
        </label>
      )}
      <input
        id={id}
        name={name}
        type={type}
        value={value}
        autoFocus={autoFocus}
        onKeyDown={onKeyDown}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="body-text"
        style={{
          width: "100%",
          height: 44,
          padding: "0 var(--s-3)",
          background: "var(--paper-2)",
          border: error ? "var(--rule-heavy)" : "var(--rule-thin)",
          borderRadius: "var(--r-1)",
          boxShadow: "var(--press-1)",
          color: "var(--ink-900)",
        }}
      />
      {error ? (
        <p className="body-strong" style={{ color: "var(--ink-900)", marginTop: "var(--s-2)" }}>
          ✗ {error}
        </p>
      ) : help ? (
        <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-2)" }}>
          {help}
        </p>
      ) : null}
    </div>
  );
}
