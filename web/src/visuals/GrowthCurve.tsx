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

/** SVG growth chart — series colors from design tokens (Refs #165). */
export default function GrowthCurve({ frame }: { frame: GrowthCurveFrame }) {
  const nValues = frame.n_values;
  const series = seriesList(frame);
  // A step teaches one class: emphasise that line and dim the rest (#161).
  const highlight = frame.highlight_label ?? null;
  const w = 320;
  const h = 160;
  const pad = { l: 36, r: 12, t: 12, b: 28 };
  const maxY = Math.max(1, ...series.flatMap((s) => s.values));
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;

  const xAt = (i: number) => pad.l + (nValues.length <= 1 ? innerW / 2 : (i / (nValues.length - 1)) * innerW);
  const yAt = (v: number) => pad.t + innerH - (v / maxY) * innerH;

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
            </g>
          );
        })}
        {nValues.map((n, i) => (
          <text key={n} x={xAt(i)} y={h - 8} textAnchor="middle" fontSize={11} fill="currentColor">
            {n}
          </text>
        ))}
        {series.map((s, si) => (
          <text
            key={`leg-${s.label}`}
            x={pad.l + 8}
            y={pad.t + 12 + si * 14}
            fontSize={11}
            fill={COLORS[si % COLORS.length]}
            fontWeight={highlight !== null && s.label === highlight ? 700 : 400}
            opacity={highlight !== null && s.label !== highlight ? 0.5 : 1}
          >
            {s.label}
          </text>
        ))}
      </svg>
    </div>
  );
}
