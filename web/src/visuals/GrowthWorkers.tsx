import type { GrowthWorkersFrame } from "../api";

export function describeGrowthWorkers(frame: GrowthWorkersFrame): string {
  const role = frame.role_label || "workers";
  return `${role} carrying boxes for n = ${frame.n_values.join(", ")}`;
}

function Stick({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x},${y})`} aria-hidden="true">
      <circle cx={0} cy={-18} r={5} fill="currentColor" />
      <line x1={0} y1={-13} x2={0} y2={4} stroke="currentColor" strokeWidth={2} />
      <line x1={0} y1={-6} x2={-8} y2={2} stroke="currentColor" strokeWidth={2} />
      <line x1={0} y1={-6} x2={8} y2={2} stroke="currentColor" strokeWidth={2} />
      <line x1={0} y1={4} x2={-6} y2={16} stroke="currentColor" strokeWidth={2} />
      <line x1={0} y1={4} x2={6} y2={16} stroke="currentColor" strokeWidth={2} />
    </g>
  );
}

function BoxPile({ count, x, baseline }: { count: number; x: number; baseline: number }) {
  const shown = Math.min(Math.max(count, 0), 12);
  const boxes = [];
  for (let i = 0; i < shown; i++) {
    const row = Math.floor(i / 2);
    const col = i % 2;
    boxes.push(
      <rect
        key={i}
        x={x - 10 + col * 12}
        y={baseline - 12 - row * 12}
        width={10}
        height={10}
        rx={1.5}
        fill="var(--primary, #3b82f6)"
        opacity={0.85}
      />,
    );
  }
  return <g>{boxes}</g>;
}

/** Stick-figure code workers with number-box piles that grow with n. */
export default function GrowthWorkers({ frame }: { frame: GrowthWorkersFrame }) {
  const nValues = frame.n_values;
  const width = Math.max(280, nValues.length * 72);
  const height = 140;
  const baseline = 110;
  // Box counts scale with n so the pile height is readable without claiming exact Big-O.
  const counts = nValues.map((n) => Math.max(1, Math.round(Math.log2(Math.max(n, 2)))));

  return (
    <div className="growth-workers" role="img" aria-label={describeGrowthWorkers(frame)}>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} className="growth-workers-svg">
        {nValues.map((n, i) => {
          const x = 36 + i * (width / nValues.length);
          return (
            <g key={n}>
              <Stick x={x} y={baseline - 20 - Math.min(counts[i], 6) * 6} />
              <BoxPile count={counts[i] * 2} x={x} baseline={baseline} />
              <text x={x} y={baseline + 18} textAnchor="middle" fontSize={12} fill="currentColor">
                n={n}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
