import type { GrowthTableFrame, GrowthTableSeries } from "../api";
import styles from "./TeachRenderBox.module.css";

function seriesList(frame: GrowthTableFrame): GrowthTableSeries[] {
  const out: GrowthTableSeries[] = [];
  if (frame.series) out.push(frame.series);
  if (frame.series_multi) out.push(...frame.series_multi);
  return out;
}

/**
 * Single current-problem hint for empty scoreboards (Refs #178).
 * Prefer empty_hint, else caption (back pointers that ground THIS probe are OK).
 * Never invent forward "counts arrive later" copy.
 */
export function emptyGrowthTableHint(frame: GrowthTableFrame): string {
  // Caption is the island figcaption — prefer it so aria matches what the learner sees.
  const caption = frame.caption?.trim();
  if (caption) return caption;
  const custom = frame.empty_hint?.trim();
  if (custom) return custom;
  return "Estimate how the step count changes as n grows.";
}

export function describeGrowthTable(frame: GrowthTableFrame): string {
  const n = frame.n_values;
  const series = seriesList(frame);
  if (series.length === 0) {
    return `Growth table for n = ${n.join(", ")}; ${emptyGrowthTableHint(frame)}`;
  }
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
    // Island already renders frame.caption as figcaption — do not repeat it here (#178).
    // Only paint an in-table note when there is no caption yet.
    const captionOnIsland = Boolean(frame.caption?.trim());
    const hint = emptyGrowthTableHint(frame);
    return (
      <div
        className={scoped ? styles.emptyProbe : "growth-table growth-table--empty"}
        role="img"
        aria-label={describeGrowthTable(frame)}
        data-testid="growth-table-empty"
      >
        {!captionOnIsland ? (
          <p className={scoped ? styles.emptyNote : "muted small growth-table-empty-note"}>{hint}</p>
        ) : null}
        <p className={scoped ? styles.emptyN : "muted small growth-table-empty-n"}>
          n = {nValues.join(", ")}
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
