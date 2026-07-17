import React from "react";

function isNumeric(v: string): boolean {
  if (v == null) return false;
  const t = v.replace(/[",$\s]/g, "");
  return t !== "" && !isNaN(Number(t));
}

/** File preview / diff table. Numbers right-aligned, tabular-nums.
 *  wrongCells: "row,col" keys get inverted ink — not red. */
export function Table({
  columns,
  rows,
  wrongCells,
  maxRows,
}: {
  columns: string[];
  rows: string[][];
  wrongCells?: Set<string>;
  maxRows?: number;
}) {
  const shown = maxRows ? rows.slice(0, maxRows) : rows;
  const zebra = shown.length > 8;
  // Detect numeric columns from the data
  const numeric = columns.map((_, c) =>
    shown.length > 0 && shown.every((r) => r[c] === "" || r[c] === undefined || isNumeric(r[c] ?? ""))
  );
  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          borderCollapse: "collapse",
          width: "100%",
          border: "var(--rule-thin)",
          borderRadius: "var(--r-0)",
        }}
      >
        <thead>
          <tr>
            {columns.map((col, c) => (
              <th
                key={c}
                className="label"
                style={{
                  background: "var(--paper-2)",
                  borderBottom: "var(--rule-thin)",
                  borderRight: c < columns.length - 1 ? "var(--rule-hair)" : undefined,
                  color: "var(--ink-500)",
                  padding: "var(--s-2) var(--s-3)",
                  textAlign: numeric[c] ? "right" : "left",
                  whiteSpace: "nowrap",
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, r) => (
            <tr
              key={r}
              style={{
                background: zebra && r % 2 === 1 ? "var(--paper-2)" : "var(--paper-1)",
              }}
            >
              {columns.map((_, c) => {
                const wrong = wrongCells?.has(`${r},${c}`);
                return (
                  <td
                    key={c}
                    className="data"
                    style={{
                      borderBottom: r < shown.length - 1 ? "var(--rule-hair)" : undefined,
                      borderRight: c < columns.length - 1 ? "var(--rule-hair)" : undefined,
                      padding: "var(--s-2) var(--s-3)",
                      textAlign: numeric[c] ? "right" : "left",
                      whiteSpace: "nowrap",
                      background: wrong ? "var(--ink-900)" : undefined,
                      color: wrong ? "var(--paper-0)" : "var(--ink-700)",
                    }}
                  >
                    {row[c] ?? ""}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
