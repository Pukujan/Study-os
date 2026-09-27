import type { GrowthTableFrame, GrowthTableSeries } from "../api";

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

export default function GrowthTable({ frame }: { frame: GrowthTableFrame }) {
  const nValues = frame.n_values;
  const series = seriesList(frame);
  const max = Math.max(1, ...series.flatMap((s) => s.values));

  return (
    <div className="growth-table" role="img" aria-label={describeGrowthTable(frame)}>
      <table className="growth-table-grid">
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
                const pct = Math.max(2, Math.round((value / max) * 100));
                return (
                  <td key={`${s.label}-${i}`}>
                    <span className="growth-table-value">{value}</span>
                    <span className="growth-table-bar" style={{ width: `${pct}%` }} aria-hidden="true" />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {series.length === 0 && <p className="muted small">Counts arrive in the next steps.</p>}
    </div>
  );
}