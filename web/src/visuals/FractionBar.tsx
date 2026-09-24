import type { FractionBarFrame } from "../api";

export function describeFractionBar(frame: FractionBarFrame): string {
  const barDescs = frame.bars.map((bar) => {
    let s = `Bar cut into ${bar.parts} equal parts, ${bar.shaded} shaded`;
    if (bar.label) s += `, labeled ${bar.label}`;
    return s;
  });
  return barDescs.join("; ") || "Fraction bar";
}

export default function FractionBar({ frame }: { frame: FractionBarFrame }) {
  const barHeight = 40;
  const barGap = 24;
  const topPad = 16;
  const bottomPad = 24;
  const width = 400;
  const height = topPad + frame.bars.length * barHeight + (frame.bars.length - 1) * barGap + bottomPad;

  return (
    <svg
      className="visual fraction-bar"
      role="img"
      aria-label={describeFractionBar(frame)}
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: "100%", maxWidth: "560px", height: "auto" }}
    >
      {frame.bars.map((bar, bi) => {
        const y = topPad + bi * (barHeight + barGap);
        const partW = (width - 64) / bar.parts;
        const x0 = 32;
        return (
          <g key={bi}>
            {Array.from({ length: bar.parts }).map((_, i) => {
              const x = x0 + i * partW;
              const shaded = i < bar.shaded;
              const highlighted = bar.highlight?.includes(i);
              return (
                <g key={i}>
                  <rect
                    x={x + 1}
                    y={y + 1}
                    width={partW - 2}
                    height={barHeight - 2}
                    rx={4}
                    className={shaded ? "fraction-bar-part shaded" : "fraction-bar-part unshaded"}
                    fill={shaded ? "var(--primary)" : "var(--paper)"}
                    stroke="var(--ink)"
                    strokeWidth={1}
                  />
                  {highlighted && (
                    <rect
                      x={x + 1}
                      y={y + 1}
                      width={partW - 2}
                      height={barHeight - 2}
                      rx={4}
                      fill="none"
                      stroke="var(--accent)"
                      strokeWidth={3}
                    />
                  )}
                </g>
              );
            })}
            {bar.label && (
              <text
                x={width / 2}
                y={y + barHeight + 16}
                textAnchor="middle"
                className="fraction-bar-label"
                style={{ fill: "var(--ink)", fontSize: 14 }}
              >
                {bar.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
