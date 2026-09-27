/**
 * Catalog interactive visual dispatcher (Refs #161 / #126).
 * Frames from interactive_exercise.py + exercise-templates.v1.json.
 */
import { useMemo, useRef, useState, type MouseEvent, type PointerEvent } from "react";
import type { InteractiveVisualFrame, GrowthMatchPanel } from "../api";

const MINI_W = 150, MINI_H = 110, PAD = { l: 28, r: 8, t: 10, b: 22 };

export function describeInteractiveVisual(frame: InteractiveVisualFrame): string {
  return frame.prompt || frame.caption || `Interactive ${frame.exercise_kind}`;
}

function valuesForShape(nValues: number[], shape: GrowthMatchPanel["shape"]): number[] {
  if (shape === "flat") return nValues.map(() => 1);
  if (shape === "linear") return nValues.map((n) => n);
  return nValues.map((n) => n * n);
}

function MiniChart({ nValues, shape, panelId }: { nValues: number[]; shape: GrowthMatchPanel["shape"]; panelId: string }) {
  const vals = valuesForShape(nValues, shape);
  const maxY = Math.max(1, ...vals);
  const innerW = MINI_W - PAD.l - PAD.r;
  const innerH = MINI_H - PAD.t - PAD.b;
  const xAt = (i: number) => PAD.l + (nValues.length <= 1 ? innerW / 2 : (i / (nValues.length - 1)) * innerW);
  const yAt = (v: number) => PAD.t + innerH - (v / maxY) * innerH;
  const pts = vals.map((v, i) => `${xAt(i)},${yAt(v)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${MINI_W} ${MINI_H}`} width="100%" height={MINI_H} data-testid={`iv-panel-${panelId}`} data-shape={shape}>
      <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={PAD.t + innerH} stroke="currentColor" opacity={0.3} />
      <line x1={PAD.l} y1={PAD.t + innerH} x2={PAD.l + innerW} y2={PAD.t + innerH} stroke="currentColor" opacity={0.3} />
      <polyline fill="none" stroke="#2563eb" strokeWidth={2.25} points={pts} />
      {nValues.map((n, i) => (
        <g key={n}>
          <circle cx={xAt(i)} cy={yAt(vals[i])} r={2.5} fill="#2563eb" />
          <text x={xAt(i)} y={MINI_H - 6} textAnchor="middle" fontSize={9} fill="currentColor">{n}</text>
        </g>
      ))}
      <text x={10} y={PAD.t + 8} fontSize={9} fill="currentColor" opacity={0.65}>{maxY}</text>
      <text x={10} y={PAD.t + innerH} fontSize={9} fill="currentColor" opacity={0.65}>0</text>
    </svg>
  );
}

const SHAPE_TO_LABEL: Record<string, string> = { flat: "O(1)", linear: "O(n)", steep: "O(n²)" };

function MatchCurves({ frame }: { frame: InteractiveVisualFrame }) {
  const panels = frame.panels || [];
  const labels = frame.labels || ["O(1)", "O(n)", "O(n²)"];
  const nValues = frame.n_values || [1, 2, 4, 8, 16];
  const [assignment, setAssignment] = useState<Record<string, string>>(() => Object.fromEntries(panels.map((p) => [p.id, ""])));
  const [result, setResult] = useState<"idle" | "pass" | "fail">("idle");
  const used = useMemo(() => new Set(Object.values(assignment).filter(Boolean)), [assignment]);
  const setLabel = (panelId: string, label: string) => {
    setResult("idle");
    setAssignment((prev) => {
      const next = { ...prev };
      if (label) for (const k of Object.keys(next)) if (k !== panelId && next[k] === label) next[k] = "";
      next[panelId] = label;
      return next;
    });
  };
  return (
    <div data-testid="iv-match-curves" data-check-result={result}>
      <p data-testid="iv-prompt">{frame.prompt}</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(9rem, 1fr))", gap: "0.75rem" }}>
        {panels.map((p) => (
          <div key={p.id} data-testid={`iv-card-${p.id}`} style={{ border: "1px solid var(--line, rgba(0,0,0,0.12))", borderRadius: "0.45rem", padding: "0.4rem" }}>
            <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>Graph {p.id}</div>
            <MiniChart nValues={nValues} shape={p.shape} panelId={p.id} />
            <label style={{ display: "block", fontSize: "0.8rem", marginTop: "0.25rem" }}>
              This is{" "}
              <select data-testid={`iv-select-${p.id}`} value={assignment[p.id]} onChange={(e) => setLabel(p.id, e.target.value)}>
                <option value="">— pick —</option>
                {labels.map((lab) => (
                  <option key={lab} value={lab} disabled={used.has(lab) && assignment[p.id] !== lab}>{lab}</option>
                ))}
              </select>
            </label>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
        <button type="button" data-testid="iv-check" onClick={() => setResult(panels.every((p) => assignment[p.id] === SHAPE_TO_LABEL[p.shape]) ? "pass" : "fail")}>Check match</button>
        {result === "pass" ? <span data-testid="iv-feedback" style={{ color: "var(--ok, #15803d)" }}>Correct match.</span> : null}
        {result === "fail" ? <span data-testid="iv-feedback" style={{ color: "var(--bad, #b91c1c)" }}>Not yet — compare flat vs rising vs rocket.</span> : null}
      </div>
    </div>
  );
}

function scoreFlat(values: number[]): number {
  const mean = values.reduce((a, b) => a + b, 0) / Math.max(values.length, 1);
  if (mean <= 0) return 0;
  const variance = values.reduce((a, v) => a + (v - mean) ** 2, 0) / values.length;
  return Math.max(0, Math.min(1, 1 - (Math.sqrt(variance) / mean) * 4));
}
function scoreCorr(values: number[], expected: number[]): number {
  const mx = expected.reduce((a, b) => a + b, 0) / expected.length;
  const my = values.reduce((a, b) => a + b, 0) / values.length;
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < expected.length; i++) {
    const a = expected[i] - mx, b = values[i] - my;
    num += a * b; dx += a * a; dy += b * b;
  }
  if (dx <= 0 || dy <= 0) return 0;
  return Math.max(0, Math.min(1, num / Math.sqrt(dx * dy)));
}

function PlotCurve({ frame }: { frame: InteractiveVisualFrame }) {
  const nValues = frame.n_values || [1, 2, 4, 8, 16];
  const target = frame.target_shape || "O(1)";
  const maxY = Math.max(...nValues.map((n) => n * n), 16);
  const W = 360, H = 180, P = { l: 40, r: 14, t: 14, b: 28 };
  const innerW = W - P.l - P.r, innerH = H - P.t - P.b;
  const [values, setValues] = useState(() => nValues.map(() => maxY / 2));
  const [result, setResult] = useState<"idle" | "pass" | "fail">("idle");
  const drag = useRef<number | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const xAt = (i: number) => P.l + (i / (nValues.length - 1)) * innerW;
  const yAt = (v: number) => P.t + innerH - (Math.max(0, Math.min(v, maxY)) / maxY) * innerH;
  const vFromY = (y: number) => Math.max(0, Math.min(maxY, ((P.t + innerH - y) / innerH) * maxY));
  const local = (cx: number, cy: number) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return { x: (cx - rect.left) * (W / Math.max(rect.width, 1)), y: (cy - rect.top) * (H / Math.max(rect.height, 1)) };
  };
  const onCheck = () => {
    let s = 0;
    if (target === "O(1)") s = scoreFlat(values);
    else if (target === "O(n)") s = scoreCorr(values, nValues.map((n) => n));
    else s = scoreCorr(values, nValues.map((n) => n * n));
    setResult(s >= 0.72 ? "pass" : "fail");
  };
  return (
    <div data-testid="iv-plot-curve" data-target-shape={target} data-check-result={result}>
      <p data-testid="iv-prompt">{frame.prompt}</p>
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} width="100%" height={H}
        onPointerMove={(e: PointerEvent) => { if (drag.current === null) return; const { y } = local(e.clientX, e.clientY); const next = [...values]; next[drag.current] = vFromY(y); setValues(next); }}
        onPointerUp={() => { drag.current = null; }} onPointerLeave={() => { drag.current = null; }}>
        <line x1={P.l} y1={P.t} x2={P.l} y2={P.t + innerH} stroke="currentColor" opacity={0.25} />
        <line x1={P.l} y1={P.t + innerH} x2={P.l + innerW} y2={P.t + innerH} stroke="currentColor" opacity={0.25} />
        <polyline fill="none" stroke="#2563eb" strokeWidth={2.5} points={values.map((v, i) => `${xAt(i)},${yAt(v)}`).join(" ")} />
        {nValues.map((n, i) => (
          <g key={n}>
            <circle cx={xAt(i)} cy={yAt(values[i])} r={9} fill="#2563eb" stroke="#fff" strokeWidth={2} style={{ cursor: "ns-resize", touchAction: "none" }}
              data-testid={`iv-dot-${i}`}
              onPointerDown={(e) => { e.preventDefault(); (e.target as Element).setPointerCapture?.(e.pointerId); drag.current = i; setResult("idle"); }} />
            <text x={xAt(i)} y={H - 8} textAnchor="middle" fontSize={11} fill="currentColor">{n}</text>
          </g>
        ))}
      </svg>
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.35rem", alignItems: "center", flexWrap: "wrap" }}>
        <button type="button" data-testid="iv-check" onClick={onCheck}>Check shape</button>
        {result === "pass" ? <span data-testid="iv-feedback" style={{ color: "var(--ok, #15803d)" }}>Shape matches {target}.</span> : null}
        {result === "fail" ? <span data-testid="iv-feedback" style={{ color: "var(--bad, #b91c1c)" }}>Not quite {target} yet.</span> : null}
      </div>
    </div>
  );
}

function PlaceNumberLine({ frame }: { frame: InteractiveVisualFrame }) {
  const max = frame.line_max ?? 1;
  const ticks = frame.ticks || [0, 0.25, 0.5, 0.75, 1];
  const target = frame.target ?? 0.5;
  const tol = frame.tolerance ?? 0.08;
  const [mark, setMark] = useState<number | null>(null);
  const [result, setResult] = useState<"idle" | "pass" | "fail">("idle");
  const width = 320, y = 36;
  const xAt = (v: number) => 24 + (v / max) * (width - 48);
  const onClick = (e: MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMark(Math.max(0, Math.min(max, ((e.clientX - rect.left - 24) / (width - 48)) * max)));
    setResult("idle");
  };
  return (
    <div data-testid="iv-place-number-line" data-check-result={result}>
      <p data-testid="iv-prompt">{frame.prompt}</p>
      <svg viewBox={`0 0 ${width} 64`} width="100%" height={64} data-testid="iv-number-line" onClick={onClick} style={{ cursor: "crosshair" }}>
        <line x1={24} y1={y} x2={width - 24} y2={y} stroke="currentColor" strokeWidth={2} />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={xAt(t)} y1={y - 6} x2={xAt(t)} y2={y + 6} stroke="currentColor" />
            <text x={xAt(t)} y={y + 20} textAnchor="middle" fontSize={10} fill="currentColor">{t}</text>
          </g>
        ))}
        {mark !== null ? <circle cx={xAt(mark)} cy={y} r={7} fill="#2563eb" data-testid="iv-mark" /> : null}
      </svg>
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.35rem", alignItems: "center" }}>
        <button type="button" data-testid="iv-check" onClick={() => mark !== null && setResult(Math.abs(mark - target) <= tol * max ? "pass" : "fail")}>Check place</button>
        {result === "pass" ? <span data-testid="iv-feedback" style={{ color: "var(--ok, #15803d)" }}>On the line — good.</span> : null}
        {result === "fail" ? <span data-testid="iv-feedback" style={{ color: "var(--bad, #b91c1c)" }}>Close — try again.</span> : null}
      </div>
    </div>
  );
}

export default function InteractiveVisual({ frame }: { frame: InteractiveVisualFrame }) {
  const kind = frame.exercise_kind;
  return (
    <div className="interactive-visual" data-testid="interactive-visual" data-exercise-kind={kind}>
      {kind === "match_curves" ? <MatchCurves frame={frame} /> : null}
      {kind === "plot_curve" ? <PlotCurve frame={frame} /> : null}
      {kind === "place_number_line" ? <PlaceNumberLine frame={frame} /> : null}
      {kind !== "match_curves" && kind !== "plot_curve" && kind !== "place_number_line" ? (
        <p>{frame.prompt || `Unsupported exercise kind: ${kind}`}</p>
      ) : null}
    </div>
  );
}
