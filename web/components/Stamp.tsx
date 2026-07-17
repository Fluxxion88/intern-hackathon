import React from "react";

/** The payoff. Appears once, on convergence. */
export function Stamp({
  title = "MATCHED",
  detail,
  animate = true,
  style,
}: {
  title?: string;
  detail: string;
  animate?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={animate ? "anim-stamp" : ""}
      style={{
        display: "inline-block",
        border: "var(--rule-heavy)",
        borderRadius: "var(--r-stamp)",
        background: "transparent",
        padding: "var(--s-3) var(--s-4)",
        color: "var(--ink-900)",
        opacity: 0.88,
        transform: animate ? undefined : "rotate(-4deg)",
        textAlign: "center",
        ...style,
      }}
    >
      <div
        className="label"
        style={{ letterSpacing: "0.18em", color: "var(--ink-900)" }}
      >
        {title}
      </div>
      <div
        style={{
          borderTop: "var(--rule-thin)",
          margin: "var(--s-1) 0",
        }}
      />
      <div className="data" style={{ fontSize: 12, color: "var(--ink-900)" }}>
        {detail}
      </div>
    </div>
  );
}
