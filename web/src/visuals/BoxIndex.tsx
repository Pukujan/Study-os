import type { BoxIndexFrame } from "../api";

export function describeBoxIndex(frame: BoxIndexFrame): string {
  const parts: string[] = [];
  parts.push(`Array [${frame.array.join(", ")}]`);
  if (frame.box) {
    parts.push(`box covers indices ${frame.box.start} through ${frame.box.start + frame.box.k - 1}`);
  }
  if (frame.arrows && frame.arrows.length > 0) {
    parts.push(`arrows at ${frame.arrows.map((a) => `${a.label} on ${a.row}`).join(", ")}`);
  }
  if (frame.sum_label) parts.push(`sum ${frame.sum_label}`);
  return parts.join("; ") || "Box index diagram";
}

export default function BoxIndex({ frame }: { frame: BoxIndexFrame }) {
  const n = frame.array.length;
  const labelW = 90;
  const margin = 24;
  const width = 400;
  const usable = width - margin * 2 - labelW;
  const cellW = n > 0 ? usable / n : usable;
  const cx = (i: number) => margin + labelW + cellW / 2 + i * cellW;

  const showPositions = frame.show_positions;
  const showIndices = frame.show_indices;

  const positionsY = 28;
  const numbersY = 62;
  const indicesY = 96;
  const arrowTop = 8;
  const arrowY = positionsY - 18;
  const height = showIndices ? 120 : 100;

  return (
    <svg
      className="visual box-index"
      role="img"
      aria-label={describeBoxIndex(frame)}
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: "100%", maxWidth: "560px", height: "auto", maxHeight: "38vh" }}
    >
      {showPositions && (
        <>
          <text x={10} y={positionsY} style={{ fill: "var(--muted)", fontSize: 11, fontWeight: 600 }}>
            positions (p)
          </text>
          {frame.array.map((_, i) => (
            <text key={`pos-${i}`} x={cx(i)} y={positionsY} textAnchor="middle" style={{ fill: "var(--muted)", fontSize: 12 }}>
              {i + 1}
            </text>
          ))}
        </>
      )}
      <text x={10} y={numbersY} style={{ fill: "var(--muted)", fontSize: 11, fontWeight: 600 }}>
        numbers (a)
      </text>
      {frame.array.map((v, i) => (
        <text
          key={`num-${i}`}
          x={cx(i)}
          y={numbersY}
          textAnchor="middle"
          style={{ fill: "var(--ink)", fontSize: 16, fontWeight: 600 }}
        >
          {v}
        </text>
      ))}
      {frame.box && (
        <rect
          x={margin + labelW + frame.box.start * cellW + 2}
          y={numbersY - 22}
          width={cellW * frame.box.k - 4}
          height={38}
          rx={6}
          fill="none"
          stroke="var(--primary)"
          strokeWidth={2}
        />
      )}
      {showIndices && (
        <>
          <text x={10} y={indicesY} style={{ fill: "var(--muted)", fontSize: 11, fontWeight: 600 }}>
            index (i)
          </text>
          {frame.array.map((_, i) => (
            <text key={`idx-${i}`} x={cx(i)} y={indicesY} textAnchor="middle" style={{ fill: "var(--muted)", fontSize: 12 }}>
              {i}
            </text>
          ))}
        </>
      )}
      {frame.arrows?.map((arrow, i) => {
        const x = cx(arrow.at);
        const y = arrow.row === "positions" ? arrowY : numbersY - 22;
        return (
          <g key={i}>
            <path d={`M ${x} ${y} L ${x - 6} ${y - arrowTop} L ${x + 6} ${y - arrowTop} Z`} fill="var(--accent)" />
            <text x={x} y={y - arrowTop - 4} textAnchor="middle" style={{ fill: "var(--ink)", fontSize: 11 }}>
              {arrow.label}
            </text>
          </g>
        );
      })}
      {frame.sum_label && (
        <text x={width / 2} y={height - 8} textAnchor="middle" style={{ fill: "var(--ink)", fontSize: 13, fontWeight: 600 }}>
          {frame.sum_label}
        </text>
      )}
    </svg>
  );
}
