import React from "react";

/** The code display. No syntax highlighting — deliberate.
 *  Bold weight on def/return keywords only. */
export function Well({
  code,
  maxHeight = 320,
}: {
  code: string;
  maxHeight?: number;
}) {
  const lines = code.replace(/\n$/, "").split("\n");
  return (
    <div
      style={{
        background: "var(--paper-2)",
        boxShadow: "var(--press-1)",
        borderRadius: "var(--r-0)",
        border: "var(--rule-thin)",
        maxHeight,
        overflow: "auto",
        padding: "var(--s-4)",
      }}
    >
      <pre className="code" style={{ margin: 0, color: "var(--ink-900)" }}>
        {lines.map((line, i) => {
          const parts = line.split(/\b(def|return)\b/);
          return (
            <div key={i} style={{ display: "flex", gap: "var(--s-3)", whiteSpace: "pre" }}>
              <span
                aria-hidden="true"
                style={{
                  color: "var(--ink-300)",
                  minWidth: 24,
                  textAlign: "right",
                  userSelect: "none",
                  flex: "none",
                }}
              >
                {i + 1}
              </span>
              <span>
                {parts.map((p, j) =>
                  p === "def" || p === "return" ? (
                    <strong key={j} style={{ fontWeight: 600 }}>
                      {p}
                    </strong>
                  ) : (
                    <React.Fragment key={j}>{p}</React.Fragment>
                  )
                )}
              </span>
            </div>
          );
        })}
      </pre>
    </div>
  );
}
