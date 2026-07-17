import React from "react";

/** The soul of the ledger slip: one tick per output cell.
 *  '1' = matches ground truth (ink-900), else doesn't (ink-100).
 *  3px wide, 14px tall divs, 1px gap. */
export function CellStrip({
  strip,
  okCount,
  total,
}: {
  strip: string;
  okCount?: number;
  total?: number;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--s-3)",
        minWidth: 0,
      }}
    >
      <div
        aria-hidden="true"
        style={{
          display: "flex",
          gap: 1,
          flexWrap: "wrap",
          minWidth: 0,
          flex: "0 1 auto",
        }}
      >
        {strip.split("").map((c, i) => (
          <div
            key={i}
            style={{
              width: 3,
              height: 14,
              background: c === "1" ? "var(--ink-900)" : "var(--ink-100)",
            }}
          />
        ))}
      </div>
      {okCount !== undefined && total !== undefined && (
        <span className="data" style={{ color: "var(--ink-700)", flex: "none" }}>
          {okCount}/{total}
        </span>
      )}
    </div>
  );
}
