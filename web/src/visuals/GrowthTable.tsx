import type { GrowthTableFrame, GrowthTableSeries } from "../api";
import styles from "./TeachRenderBox.module.css";

function seriesList(frame: GrowthTableFrame): GrowthTableSeries[] {
  const out: GrowthTableSeries[] = [];
  if (frame.series) out.push(frame.series);
  if (frame.series_multi) out.push(...frame.series_multi);
  return out;
}

export function describeGrowthTable(frame: GrowthTableFrame): string {
  const n = frame.n_values;
  const series = seriesList(frame);
  if (series.length === 0) return `Growth table for n = ${n.join(", ")}`;
  const parts = series.map((s) => `${s.label}: ${s.values.join(", ")}`);
  return `Growth table for n = ${n.join(", ")}; ${parts.join("; ")}`;
}

type Props = { frame: GrowthTableFrame; scoped?: boolean };

/** Compact scoreboard. Island CSS owns layout when scoped. */
export default function GrowthTable({ frame, scoped = false }: Props) {
  const nValues = frame.n_values;
  const series = seriesList(frame);
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const rootClass = scoped ? styles.scoreboard : "growth-table";

  if (series.length === 0) {
    return (
      <div
        className={scoped ? undefined : "growth-table growth-table--empty"}
        role="img"
        aria-label={describeGrowthTable(frame)}
      >
        <div className={scoped ? styles.chips : "growth-scoreboard-chips"}>
          <span className={scoped ? styles.chipLabel : "growth-scoreboard-chip growth-scoreboard-chip--label"}>n</span>
          {nValues.map((value, i) => (
            <span key={`n-${i}`} className={scoped ? styles.chip : "growth-scoreboard-chip"}>
              {value}
            </span>
          ))}
        </div>
        <p className={scoped ? styles.emptyNote : "muted small growth-table-empty-note"}>
          Counts arrive in the next steps.
        </p>
      </div>
    );
  }

  return (
    <div className={rootClass} role="img" aria-label={describeGrowthTable(frame)}>
      <table className={scoped ? undefined : "growth-table-grid growth-scoreboard"}>
        <thead>
          <tr>
            <th scope="col">n</th>
            {nValues.map((value, i) => (
              <th key={`n-${i}`} scope="col">
                {value}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {series.map((s) => (
            <tr key={s.label}>
              <th scope="row">{s.label}</th>
              {nValues.map((_, i) => {
                const value = s.values[i] ?? 0;
                const pct = Math.max(8, Math.round((value / max) * 100));
                return (
                  <td key={`${s.label}-${i}`}>
                    <span className={scoped ? styles.cell : "growth-table-cell"}>
                      <span className={scoped ? styles.value : "growth-table-value"}>{value}</span>
                      <span
                        className={scoped ? styles.bar : "growth-table-bar"}
                        style={{ width: `${pct}%` }}
                        aria-hidden="true"
                      />
                    </span>
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
