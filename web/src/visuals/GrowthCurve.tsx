import type { GrowthCurveFrame, GrowthTableSeries } from "../api";

function seriesList(frame: GrowthCurveFrame): GrowthTableSeries[] {
  const out: GrowthTableSeries[] = [];
  if (frame.series) out.push(frame.series);
  if (frame.series_multi) out.push(...frame.series_multi);
  return out;
}

export function describeGrowthCurve(frame: GrowthCurveFrame): string {
  const series = seriesList(frame);
  const scale = frame.y_scale === "log" ? "log scale" : "linear scale";
  if (!series.length) return `Growth chart (${scale}) for n = ${frame.n_values.join(", ")}`;
  return `Growth chart (${scale}) for n = ${frame.n_values.join(", ")}; ${series.map((s) => s.label).join(", ")}`;
}

const COLORS = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2"];

function yTransform(v: number, maxY: number, log: boolean): number {
  const safe = Math.max(v, 0);
  if (!log) return safe / Math.max(maxY, 1);
  const minV = 1;
  const lv = Math.log10(Math.max(safe, minV));
  const lmax = Math.log10(Math.max(maxY, minV));
  return lmax <= 0 ? 0 : lv / lmax;
}

/** Multi-class growth chart (O(1)/log n/n/n² family). SVG now; Pixi later. */
export default function GrowthCurve({ frame }: { frame: GrowthCurveFrame }) {
  const nValues = frame.n_values;
  const series = seriesList(frame);
  const log = frame.y_scale === "log";
  const highlight = frame.highlight_label || null;
  const w = 360;
  const h = 200;
  const pad = { l: 40, r: 14, t: 14, b: 32 };
  const maxY = Math.max(1, ...series.flatMap((s) => s.values));
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const legendH = Math.max(0, series.length * 14);
  const chartH = h + legendH;

  const xAt = (i: number) => pad.l + (nValues.length <= 1 ? innerW / 2 : (i / (nValues.length - 1)) * innerW);
  const yAt = (v: number) => pad.t + innerH - yTransform(v, maxY, log) * innerH;

  return (
    <div
      className="growth-curve"
      data-testid="growth-curve"
      data-y-scale={log ? "log" : "linear"}
      data-asset-id={frame.asset_id || undefined}
      role="img"
      aria-label={describeGrowthCurve(frame)}
    >
      <svg viewBox={`0 0 ${w} ${chartH}`} width="100%" height={chartH} className="growth-curve-svg">
        <line x1={pad.l} y1={pad.t} x2={pad.l} y2={pad.t + innerH} stroke="currentColor" opacity={0.25} />
        <line x1={pad.l} y1={pad.t + innerH} x2={pad.l + innerW} y2={pad.t + innerH} stroke="currentColor" opacity={0.25} />
        <text x={8} y={pad.t + 8} fontSize={10} fill="currentColor" opacity={0.7}>
          {log ? "ops (log)" : "ops"}
        </text>
        {series.map((s, si) => {
          const pts = nValues.map((_, i) => `${xAt(i)},${yAt(s.values[i] ?? 0)}`).join(" ");
          const isHi = highlight === s.label;
          return (
            <g key={s.label} opacity={highlight && !isHi ? 0.45 : 1}>
              <polyline
                fill="none"
                stroke={COLORS[si % COLORS.length]}
                strokeWidth={isHi ? 3.5 : 2.25}
                points={pts}
              />
              {nValues.map((_, i) => (
                <circle
                  key={`${s.label}-${i}`}
                  cx={xAt(i)}
                  cy={yAt(s.values[i] ?? 0)}
                  r={isHi ? 4 : 3}
                  fill={COLORS[si % COLORS.length]}
                />
              ))}
            </g>
          );
        })}
        {nValues.map((n, i) => (
          <text key={n} x={xAt(i)} y={h - 10} textAnchor="middle" fontSize={11} fill="currentColor">
            {n}
          </text>
        ))}
        <text x={pad.l + innerW / 2} y={h - 0} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.7}>
          n
        </text>
        {series.map((s, si) => (
          <text
            key={`leg-${s.label}`}
            x={pad.l + 4}
            y={h + 12 + si * 14}
            fontSize={11}
            fontWeight={highlight === s.label ? 700 : 400}
            fill={COLORS[si % COLORS.length]}
          >
            {s.label}
          </text>
        ))}
      </svg>
    </div>
  );
}
