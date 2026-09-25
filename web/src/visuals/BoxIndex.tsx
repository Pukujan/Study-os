import type { BoxIndexFrame } from "../api";

export function describeBoxIndex(frame: BoxIndexFrame): string {
  const parts: string[] = [];
  parts.push(`Array [${frame.array.join(", ")}]`);
  if (frame.box) {
    parts.push(`box covers indices ${frame.box.start} through ${frame.box.start + frame.box.k - 1}`);
    if (frame.box.brace_label) parts.push(`brace label ${frame.box.brace_label}`);
  }
  if (frame.circles && frame.circles.length > 0) {
    parts.push(`circled indices ${frame.circles.join(", ")}`);
  }
  if (frame.arrows && frame.arrows.length > 0) {
    parts.push(
      `arrows ${frame.arrows.map((a) => `${a.label} at ${a.at} on ${a.row}${a.dir ? " " + a.dir : ""}`).join("; ")}`,
    );
  }
  if (frame.sum_label) parts.push(`sum ${frame.sum_label}`);
  return parts.join("; ") || "Box index diagram";
}

export type BoxIndexProps = {
  frame: BoxIndexFrame;
  onSelectIndex?: (i: number) => void;
};

export default function BoxIndex({ frame, onSelectIndex }: BoxIndexProps) {
  const n = frame.array.length;
  const labelW = 90;
  const margin = 24;
  const width = 400;
  const usable = width - margin * 2 - labelW;
  const cellW = n > 0 ? usable / n : usable;
  const cx = (i: number) => margin + labelW + cellW / 2 + i * cellW;

  const showPositions = frame.show_positions;
  const showIndices = frame.show_indices;

  const rowGap = 32;
  const topPad = 16;

  // Vertical order: arrow-down labels, index, positions, numbers, arrow-up labels, brace, sum.
  let y = topPad;

  // Reserve space for any downward arrow labels above their target row.
  const downArrows = frame.arrows?.filter((a) => !a.dir || a.dir === "down") ?? [];
  const upArrows = frame.arrows?.filter((a) => a.dir === "up") ?? [];

  const hasDown = downArrows.length > 0;
  const arrowDownTop = hasDown ? y + 4 : y;
  if (hasDown) y += 18;

  const indexY = showIndices ? y + 16 : -1;
  if (showIndices) y += rowGap;

  const positionsY = showPositions ? y + 16 : -1;
  if (showPositions) y += rowGap;

  const numbersY = y + 16;
  y += rowGap;

  // Up arrows below numbers row.
  const arrowUpY = upArrows.length > 0 ? y + 4 : y;
  if (upArrows.length > 0) y += 18;

  const box = frame.box;
  const braceTop = y;
  const braceHeight = 14;
  const braceY = braceTop + braceHeight - 4;

  const braceLabel = box?.brace_label ?? (box ? "box" : null);
  const kLabel = box ? box.k === 1 ? "k = 1" : `k = ${box.k}` : null;
  const bottomText = braceLabel || kLabel;
  const sumLabel = frame.sum_label;

  const height = braceY + 14 + (bottomText ? 14 : 0) + (sumLabel ? 14 : 0) + 8;

  const cellHitW = cellW;
  const cellHitH = 28;

  return (
    <svg
      className="visual box-index"
      role="img"
      aria-label={describeBoxIndex(frame)}
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: "100%", maxWidth: "560px", height: "auto", maxHeight: "42vh" }}
    >
      {/* Subtle highlight fill behind boxed cells */}
      {box && (
        <rect
          x={cx(box.start) - cellW / 2 + 2}
          y={numbersY - 16}
          width={cellW * box.k - 4}
          height={26}
          rx={4}
          fill="var(--primary)"
          fillOpacity={0.08}
          stroke="none"
        />
      )}

      {/* Index row */}
      {showIndices && (
        <>
          <text x={10} y={indexY} style={{ fill: "var(--muted)", fontSize: 12, fontWeight: 600, fontFamily: "ui-monospace, monospace" }}>
            index(i)
          </text>
          {frame.array.map((_, i) => (
            <text
              key={`idx-${i}`}
              x={cx(i)}
              y={indexY}
              textAnchor="middle"
              style={{ fill: "var(--muted)", fontSize: 14, fontFamily: "ui-monospace, monospace" }}
            >
              {i}
            </text>
          ))}
        </>
      )}

      {/* Positions row */}
      {showPositions && (
        <>
          <text x={10} y={positionsY} style={{ fill: "var(--muted)", fontSize: 12, fontWeight: 600, fontFamily: "ui-monospace, monospace" }}>
            positions(p)
          </text>
          {frame.array.map((_, i) => (
            <text
              key={`pos-${i}`}
              x={cx(i)}
              y={positionsY}
              textAnchor="middle"
              style={{ fill: "var(--muted)", fontSize: 14, fontFamily: "ui-monospace, monospace" }}
            >
              {i + 1}
            </text>
          ))}
        </>
      )}

      {/* Number cell chrome — golden chart look even without a window box */}
      {frame.array.map((_, i) => (
        <rect
          key={`cell-${i}`}
          x={cx(i) - Math.min(cellW * 0.42, 22)}
          y={numbersY - 18}
          width={Math.min(cellW * 0.84, 44)}
          height={28}
          rx={6}
          fill="var(--card, #fff)"
          stroke="var(--line, #d7d2ef)"
          strokeWidth={1.5}
        />
      ))}

      {/* Numbers row */}
      <text x={10} y={numbersY} style={{ fill: "var(--muted)", fontSize: 12, fontWeight: 600, fontFamily: "ui-monospace, monospace" }}>
        numbers(a)
      </text>
      {frame.array.map((v, i) => (
        <text
          key={`num-${i}`}
          x={cx(i)}
          y={numbersY + 2}
          textAnchor="middle"
          style={{ fill: "var(--ink)", fontSize: 16, fontWeight: 700, fontFamily: "ui-monospace, monospace" }}
        >
          {v}
        </text>
      ))}

      {/* Circles around cell values */}
      {frame.circles?.map((i) =>
        i >= 0 && i < n ? (
          <ellipse
            key={`circle-${i}`}
            cx={cx(i)}
            cy={numbersY - 4}
            rx={Math.max(10, cellW * 0.4)}
            ry={14}
            fill="none"
            stroke="var(--accent)"
            strokeWidth={2}
          />
        ) : null
      )}

      {/* Interactive cell buttons */}
      {frame.interactive &&
        frame.array.map((_, i) => (
          <g key={`hit-${i}`}>
            <rect
              x={cx(i) - cellHitW / 2}
              y={numbersY - cellHitH / 2}
              width={cellHitW}
              height={cellHitH}
              fill="transparent"
              stroke="none"
              cursor="pointer"
              onClick={() => onSelectIndex?.(i)}
              role="button"
              aria-label={`Select index ${i}`}
            />
          </g>
        ))}

      {/* Down arrows (from above, pointing down) */}
      {downArrows.map((arrow, i) => {
        const x = cx(arrow.at);
        let targetY = numbersY - 10;
        if (arrow.row === "indices") targetY = indexY - 6;
        if (arrow.row === "positions") targetY = positionsY - 6;
        const tipY = targetY + 8;
        const labelY = arrowDownTop + 12;
        return (
          <g key={`down-${i}`}>
            <line x1={x} y1={labelY + 8} x2={x} y2={tipY} stroke="var(--accent)" strokeWidth={2} markerEnd="url(#arrowhead-down)" />
            <text
              x={x}
              y={labelY}
              textAnchor="middle"
              style={{ fill: "var(--ink)", fontSize: 12, fontFamily: "ui-monospace, monospace" }}
            >
              {arrow.label}
            </text>
          </g>
        );
      })}

      {/* Up arrows (from below, pointing up) */}
      {upArrows.map((arrow, i) => {
        const x = cx(arrow.at);
        const startY = numbersY + 10;
        const tipY = numbersY - 4;
        const labelY = arrowUpY + 18;
        return (
          <g key={`up-${i}`}>
            <line x1={x} y1={startY} x2={x} y2={tipY} stroke="var(--accent)" strokeWidth={2} markerEnd="url(#arrowhead-up)" />
            <text
              x={x}
              y={labelY}
              textAnchor="middle"
              style={{ fill: "var(--ink)", fontSize: 12, fontFamily: "ui-monospace, monospace" }}
            >
              {arrow.label}
            </text>
          </g>
        );
      })}

      {/* Box brace */}
      {box && (
        <g>
          <title>{`└── ${bottomText || "box"} ──┘`}</title>
          <path
            d={`M ${cx(box.start) - cellW / 2 + 4} ${braceTop} L ${cx(box.start) - cellW / 2 + 4} ${braceY} L ${
              cx(box.start + box.k - 1) + cellW / 2 - 4
            } ${braceY} L ${cx(box.start + box.k - 1) + cellW / 2 - 4} ${braceTop}`}
            fill="none"
            stroke="var(--ink)"
            strokeWidth={2}
          />
          {bottomText && (
            <text
              x={width / 2}
              y={braceY + 14}
              textAnchor="middle"
              style={{ fill: "var(--ink)", fontSize: 13, fontWeight: 600, fontFamily: "ui-monospace, monospace" }}
            >
              {bottomText}
            </text>
          )}
        </g>
      )}

      {sumLabel && (
        <text
          x={width / 2}
          y={braceY + 14 + (bottomText ? 16 : 0)}
          textAnchor="middle"
          style={{ fill: "var(--ink)", fontSize: 13, fontWeight: 600, fontFamily: "ui-monospace, monospace" }}
        >
          {sumLabel}
        </text>
      )}

      {/* Arrow markers */}
      <defs>
        <marker id="arrowhead-down" markerWidth="8" markerHeight="8" refX="4" refY="2" orient="auto">
          <path d="M0,0 L8,0 L4,6 Z" fill="var(--accent)" />
        </marker>
        <marker id="arrowhead-up" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
          <path d="M0,6 L8,6 L4,0 Z" fill="var(--accent)" />
        </marker>
      </defs>
    </svg>
  );
}
