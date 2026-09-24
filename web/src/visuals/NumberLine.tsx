function parseValue(at: string): number {
  const trimmed = at.trim();
  if (trimmed.includes("/")) {
    const [num, den] = trimmed.split("/");
    const n = Number(num);
    const d = Number(den);
    if (!Number.isNaN(n) && !Number.isNaN(d) && d !== 0) return n / d;
  }
  return Number(trimmed);
}

export function describeNumberLine(max: number, marks: { at: string; label: string }[]): string {
  const markText = marks.map((m) => m.label || m.at).join(", ") || "none";
  return `Number line from 0 to ${max} with marks at ${markText}`;
}

export default function NumberLine({ max, ticks, marks }: { max: number; ticks: number; marks: { at: string; label: string }[] }) {
  const width = 400;
  const height = 60;
  const pad = 24;
  const lineY = height / 2;
  const scale = (width - pad * 2) / max;

  const tickCount = Math.max(2, ticks + 1);

  return (
    <svg
      className="visual number-line"
      role="img"
      aria-label={describeNumberLine(max, marks)}
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: "100%", maxWidth: "560px", height: "auto" }}
    >
      <line x1={pad} y1={lineY} x2={width - pad} y2={lineY} stroke="var(--ink)" strokeWidth={2} />
      {Array.from({ length: tickCount }).map((_, i) => {
        const x = pad + (i * (width - pad * 2)) / (tickCount - 1);
        return <line key={i} x1={x} y1={lineY - 6} x2={x} y2={lineY + 6} stroke="var(--ink)" strokeWidth={2} />;
      })}
      {marks.map((m, i) => {
        const x = pad + parseValue(m.at) * scale;
        return (
          <g key={i}>
            <circle cx={x} cy={lineY} r={5} fill="var(--accent)" />
            <text x={x} y={lineY - 10} textAnchor="middle" className="number-line-mark-label" style={{ fill: "var(--ink)", fontSize: 12 }}>
              {m.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
