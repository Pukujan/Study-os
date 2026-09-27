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

/** Fallback palette by series index (design tokens). */
const COLORS = [
  "var(--chart-1, var(--primary))",
  "var(--chart-2, var(--bad))",
  "var(--chart-3, var(--ok))",
  "var(--chart-4, var(--gold))",
];

/**
 * Textbook 4-class colors (attachment: Big O Notation with Input Size / Time):
 * O(1) green, O(log n) gold, O(n) blue, O(n²) red — labels match curve stroke.
 */
function colorForSeries(label: string, index: number): string {
  const key = label.replace(/\s+/g, "").toLowerCase();
  if (key === "o(1)") return "var(--chart-3, var(--ok))";
  if (key === "o(logn)" || key === "o(log₂n)" || key === "o(log2n)") {
    return "var(--chart-4, var(--gold))";
  }
  if (key === "o(n)") return "var(--chart-1, var(--primary))";
  if (key === "o(n²)" || key === "o(n^2)" || key === "o(n2)") {
    return "var(--chart-2, var(--bad))";
  }
  return COLORS[index % COLORS.length]!;
}

/**
 * SVG growth chart — textbook end-of-line labels in curve color (Refs #179).
 * No separate swatch legend: labels sit just past each line's right end.
 */
export default function GrowthCurve({ frame }: { frame: GrowthCurveFrame }) {
  const nValues = frame.n_values;
  const series = seriesList(frame);
  // A step teaches one class: emphasise that line and dim the rest (#161).
  const highlight = frame.highlight_label ?? null;
  const w = 380;
  const h = 188;
  // Left/bottom room for axis titles; right pad for end-of-line labels.
  const pad = { l: 48, r: 62, t: 16, b: 40 };
  const maxY = Math.max(1, ...series.flatMap((s) => s.values));
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;

  const xAt = (i: number) =>
    pad.l + (nValues.length <= 1 ? innerW / 2 : (i / (nValues.length - 1)) * innerW);
  const yAt = (v: number) => pad.t + innerH - (v / maxY) * innerH;

  // Stack end labels that would collide (same y).
  const endLabelY = (() => {
    const raw = series.map((s) => yAt(s.values[nValues.length - 1] ?? 0));
    const sorted = raw.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
    const placed = [...raw];
    const minGap = 13;
    for (let k = 1; k < sorted.length; k++) {
      const prev = sorted[k - 1]!;
      const cur = sorted[k]!;
      if (placed[cur.i]! - placed[prev.i]! < minGap) {
        placed[cur.i] = placed[prev.i]! + minGap;
      }
    }
    return placed;
  })();

  const axisStroke = "var(--chart-axis, currentColor)";

  return (
    <div className="growth-curve" role="img" aria-label={describeGrowthCurve(frame)}>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" height={h} className="growth-curve-svg">
        {/* Clean axes (textbook: Input size / Time) */}
        <line
          x1={pad.l}
          y1={pad.t}
          x2={pad.l}
          y2={pad.t + innerH}
          stroke={axisStroke}
          opacity={0.45}
        />
        <line
          x1={pad.l}
          y1={pad.t + innerH}
          x2={pad.l + innerW}
          y2={pad.t + innerH}
          stroke={axisStroke}
          opacity={0.45}
        />
        <text
          className="growth-curve-axis-y"
          x={14}
          y={pad.t + innerH / 2}
          textAnchor="middle"
          fontSize={10}
          fill="currentColor"
          opacity={0.7}
          transform={`rotate(-90 14 ${pad.t + innerH / 2})`}
        >
          Time →
        </text>
        <text
          className="growth-curve-axis-x"
          x={pad.l + innerW / 2}
          y={h - 6}
          textAnchor="middle"
          fontSize={10}
          fill="currentColor"
          opacity={0.7}
        >
          Input size →
        </text>

        {series.map((s, si) => {
          const color = colorForSeries(s.label, si);
          const pts = nValues.map((_, i) => `${xAt(i)},${yAt(s.values[i] ?? 0)}`).join(" ");
          const isHighlight = highlight !== null && s.label === highlight;
          const dimmed = highlight !== null && !isHighlight;
          const lastI = Math.max(0, nValues.length - 1);
          const endX = xAt(lastI);
          const endY = endLabelY[si] ?? yAt(s.values[lastI] ?? 0);
          return (
            <g key={s.label} opacity={dimmed ? 0.35 : 1}>
              <polyline
                fill="none"
                stroke={color}
                strokeWidth={isHighlight ? 3.5 : 2.5}
                points={pts}
              />
              {nValues.map((_, i) => (
                <circle
                  key={`${s.label}-${i}`}
                  cx={xAt(i)}
                  cy={yAt(s.values[i] ?? 0)}
                  r={isHighlight ? 4 : 3}
                  fill={color}
                />
              ))}
              {/* End-of-line label in the SAME color as the curve (textbook style). */}
              <text
                className="growth-curve-end-label"
                data-series-label={s.label}
                x={endX + 7}
                y={endY + 4}
                fontSize={11}
                fill={color}
                fontWeight={isHighlight ? 700 : 600}
              >
                {s.label}
              </text>
            </g>
          );
        })}
        {nValues.map((n, i) => (
          <text
            key={n}
            x={xAt(i)}
            y={pad.t + innerH + 14}
            textAnchor="middle"
            fontSize={11}
            fill="currentColor"
            opacity={0.85}
          >
            {n}
          </text>
        ))}
      </svg>
    </div>
  );
}
