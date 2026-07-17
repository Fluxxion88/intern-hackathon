import React from "react";

export function Sheet({
  elevation = 1,
  padded = true,
  className = "",
  style,
  children,
}: {
  elevation?: 0 | 1 | 2;
  padded?: boolean;
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}) {
  const shadow =
    elevation === 0 ? "var(--lift-0)" : elevation === 2 ? "var(--lift-2)" : "var(--lift-1)";
  return (
    <div
      className={className}
      style={{
        background: "var(--paper-1)",
        border: "var(--rule-thin)",
        borderRadius: "var(--r-2)",
        boxShadow: shadow,
        padding: padded ? "var(--s-5)" : 0,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
