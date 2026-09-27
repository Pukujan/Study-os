import type { GrowthCurveFrame, GrowthTableSeries } from "../api";

function seriesList(frame: GrowthCurveFrame): GrowthTableSeries[] {
  const out: GrowthTableSeries[] = [];
  if (frame.series) out.push(frame.series);
  if (frame.series_multi) out.push(...frame.series_multi);
  return out;
}

export function describeGrowthCurve(frame: GrowthCurveFrame): string {
  const series = seriesList(frame);
  if (!series.length) return `Growth chart for n = ${frame.n_values.join(", ")}`;
  const base = `Growth chart for n = ${frame.n_values.join(", ")}; ${series.map((s) => s.label).join(", ")}`;
  const highlight = frame.highlight_label;
  if (highlight && series.some((s) => s.label === highlight)) {
    return `${base}; highlighting ${highlight}`;
  }
  return base;
}

const COLORS = [
  "var(--chart-1, var(--primary))",
  "var(--chart-2, var(--bad))",
  "var(--chart-3, var(--ok))",
  "var(--chart-4, var(--gold))",
];

/** SVG growth chart — end-of-line labels + color legend (Refs #179 #165). */
export default function GrowthCurve({ frame }: { frame: GrowthCurveFrame }) {
  const nValues = frame.n_values;
  const series = seriesList(frame);
  // A step teaches one class: emphasise that line and dim the rest (#161).
  const highlight = frame.highlight_label ?? null;
  const w = 360;
  const h = 168;
  // Extra right pad so end-of-line labels fit without clipping.
  const pad = { l: 36, r: 56, t: 14, b: 28 };
  const maxY = Math.max(1, ...series.flatMap((s) => s.values));
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;

  const xAt = (i: number) => pad.l + (nValues.length <= 1 ? innerW / 2 : (i / (nValues.length - 1)) * innerW);
  const yAt = (v: number) => pad.t + innerH - (v / maxY) * innerH;

  // Stack end labels that would collide (same y).
  const endLabelY = (() => {
    const raw = series.map((s) => yAt(s.values[nValues.length - 1] ?? 0));
    const sorted = raw.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
    const placed = [...raw];
    const minGap = 12;
    for (let k = 1; k < sorted.length; k++) {
      const prev = sorted[k - 1]!;
      const cur = sorted[k]!;
      if (placed[cur.i]! - placed[prev.i]! < minGap) {
        placed[cur.i] = placed[prev.i]! + minGap;
      }
    }
    return placed;
  })();

  return (
    <div className="growth-curve" role="img" aria-label={describeGrowthCurve(frame)}>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" height={h} className="growth-curve-svg">
        <line x1={pad.l} y1={pad.t} x2={pad.l} y2={pad.t + innerH} stroke="currentColor" opacity={0.25} />
        <line x1={pad.l} y1={pad.t + innerH} x2={pad.l + innerW} y2={pad.t + innerH} stroke="currentColor" opacity={0.25} />
        {series.map((s, si) => {
          const pts = nValues
            .map((_, i) => `${xAt(i)},${yAt(s.values[i] ?? 0)}`)
            .join(" ");
          const isHighlight = highlight !== null && s.label === highlight;
          const dimmed = highlight !== null && !isHighlight;
          const lastI = Math.max(0, nValues.length - 1);
          const endX = xAt(lastI);
          const endY = endLabelY[si] ?? yAt(s.values[lastI] ?? 0);
          return (
            <g key={s.label} opacity={dimmed ? 0.35 : 1}>
              <polyline
                fill="none"
                stroke={COLORS[si % COLORS.length]}
                strokeWidth={isHighlight ? 3.5 : 2.5}
                points={pts}
              />
              {nValues.map((_, i) => (
                <circle
                  key={`${s.label}-${i}`}
                  cx={xAt(i)}
                  cy={yAt(s.values[i] ?? 0)}
                  r={isHighlight ? 4 : 3}
                  fill={COLORS[si % COLORS.length]}
                />
              ))}
              <text
                className="growth-curve-end-label"
                data-series-label={s.label}
                x={endX + 6}
                y={endY + 4}
                fontSize={11}
                fill={COLORS[si % COLORS.length]}
                fontWeight={isHighlight ? 700 : 600}
              >
                {s.label}
              </text>
            </g>
          );
        })}
        {nValues.map((n, i) => (
          <text key={n} x={xAt(i)} y={h - 8} textAnchor="middle" fontSize={11} fill="currentColor">
            {n}
          </text>
        ))}
      </svg>
      {series.length > 0 && (
        <ul className="growth-curve-legend" aria-hidden="true">
          {series.map((s, si) => {
            const isHighlight = highlight !== null && s.label === highlight;
            const dimmed = highlight !== null && !isHighlight;
            return (
              <li
                key={`leg-${s.label}`}
                className="growth-curve-legend-item"
                style={{ opacity: dimmed ? 0.5 : 1, fontWeight: isHighlight ? 700 : 400 }}
              >
                <span
                  className="growth-curve-legend-swatch"
                  style={{ background: COLORS[si % COLORS.length] }}
                />
                {s.label}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
