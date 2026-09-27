/**
 * Interactive sticks-and-boxes Big O teach visual (#185).
 *
 * Learner acts as the computer: Put Next Stick / Finished / Reset under
 * O(1) / O(n) / O(n²) rules. UX class grounded on the user-validated Gemini
 * exemplar (see content/teach-visuals/_research/big-o/sticks-boxes-gemini-exemplar/).
 */
import { useMemo, useState } from "react";
import type { SticksBoxesComplexityFrame } from "../api";
import styles from "./SticksBoxesComplexity.module.css";
import cssText from "./SticksBoxesComplexity.module.css?inline";

export type ComplexityMode = "O(1)" | "O(n)" | "O(n²)";

const MODE_OPTIONS: { value: ComplexityMode; label: string; title: string }[] = [
  { value: "O(1)", label: "O(1)", title: "Constant — 1 stick in first box" },
  { value: "O(n)", label: "O(n)", title: "Linear — 1 stick in each box" },
  { value: "O(n²)", label: "O(n²)", title: "Quadratic — cross-pair every box" },
];

const DEFAULT_N_MIN = 2;
const DEFAULT_N_MAX = 8;

function clamp(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

export function targetSticks(mode: ComplexityMode, n: number): number {
  if (mode === "O(1)") return 1;
  if (mode === "O(n)") return n;
  return n * n;
}

/** Destination box index for the stick at `placed` (0-based op about to run). */
export function destinationBox(mode: ComplexityMode, n: number, placed: number): number | null {
  const target = targetSticks(mode, n);
  if (placed < 0 || placed >= target) return null;
  if (mode === "O(1)") return 0;
  if (mode === "O(n)") return placed;
  // O(n²): stick goes into outer index i for pair (i, j) in row-major order.
  const i = Math.floor(placed / n);
  return i;
}

/** Current cross-pair (i, j) for the next stick under O(n²), else null. */
export function currentPair(mode: ComplexityMode, n: number, placed: number): { i: number; j: number } | null {
  if (mode !== "O(n²)") return null;
  const target = targetSticks(mode, n);
  if (placed < 0 || placed >= target) return null;
  const i = Math.floor(placed / n);
  const j = placed % n;
  return { i, j };
}

export function describeSticksBoxesComplexity(frame: SticksBoxesComplexityFrame): string {
  const mode = frame.initial_complexity || "O(1)";
  const n = frame.initial_n ?? 2;
  return frame.caption || `Sticks and boxes for ${mode} with n = ${n}`;
}

function emptyCounts(n: number): number[] {
  return Array.from({ length: n }, () => 0);
}

export default function SticksBoxesComplexity({ frame }: { frame: SticksBoxesComplexityFrame }) {
  const nMin = frame.n_min ?? DEFAULT_N_MIN;
  const nMax = frame.n_max ?? DEFAULT_N_MAX;
  const startN = clamp(frame.initial_n ?? nMin, nMin, nMax);
  const startMode = (frame.initial_complexity || "O(1)") as ComplexityMode;

  const [mode, setMode] = useState<ComplexityMode>(startMode);
  const [n, setN] = useState(startN);
  const [counts, setCounts] = useState<number[]>(() => emptyCounts(startN));
  const [placed, setPlaced] = useState(0);

  const target = targetSticks(mode, n);
  const finished = placed >= target;
  const nextDest = destinationBox(mode, n, placed);
  const pair = currentPair(mode, n, placed);

  const stepLabel = useMemo(() => {
    if (mode !== "O(n²)" || finished || !pair) return null;
    return `Box ${pair.i} × Box ${pair.j}`;
  }, [mode, finished, pair, placed]);

  function resetProgress(nextN = n, _nextMode = mode) {
    setCounts(emptyCounts(nextN));
    setPlaced(0);
  }

  function onModeChange(next: ComplexityMode) {
    setMode(next);
    resetProgress(n, next);
  }

  function onNChange(nextN: number) {
    const clamped = clamp(nextN, nMin, nMax);
    setN(clamped);
    resetProgress(clamped, mode);
  }

  function putNextStick() {
    if (finished) return;
    const dest = destinationBox(mode, n, placed);
    if (dest == null) return;
    setCounts((prev) => {
      const next = prev.slice();
      if (dest >= 0 && dest < next.length) next[dest] += 1;
      return next;
    });
    setPlaced((p) => p + 1);
  }

  return (
    <div
      className={styles.root}
      data-testid="sticks-boxes-complexity"
      data-complexity={mode}
      data-n={n}
      data-placed={placed}
      data-target={target}
      role="group"
      aria-label={describeSticksBoxesComplexity(frame)}
    >
      <style>{cssText}</style>
      <div className={styles.stage}>
        <div className={styles.dispenser}>
          <div className={styles.dispenserTray} aria-hidden="true">
            {!finished ? <div className={styles.dispenserStick} /> : null}
          </div>
          <span className={styles.dispenserLabel}>Sticks</span>
        </div>

        <div className={styles.boxesRow}>
          {counts.map((count, idx) => {
            const isDest = !finished && nextDest === idx;
            const isPairI = Boolean(pair && pair.i === idx);
            const isPairJ = Boolean(pair && pair.j === idx && pair.i !== pair.j);
            const boxClass = [
              styles.box,
              mode === "O(n²)" && isPairI ? styles.boxPairSource : "",
              mode === "O(n²)" && isPairJ ? styles.boxPairTarget : "",
              mode !== "O(n²)" && isDest ? styles.boxActive : "",
              mode === "O(n²)" && isPairI && pair && pair.i === pair.j ? styles.boxActive : "",
            ]
              .filter(Boolean)
              .join(" ");
            const labelClass = [
              styles.boxLabel,
              mode === "O(n²)" && isPairJ
                ? styles.boxLabelPair
                : isDest || isPairI
                  ? styles.boxLabelActive
                  : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <div key={idx} className={styles.boxWrap}>
                {isDest ? (
                  <span className={styles.dropCue} aria-hidden="true">
                    ↓
                  </span>
                ) : (
                  <span className={styles.dropCue} style={{ visibility: "hidden" }} aria-hidden="true">
                    ↓
                  </span>
                )}
                <div
                  className={boxClass}
                  data-testid={`sticks-box-${idx}`}
                  data-active={isDest || isPairI ? "true" : "false"}
                  data-pair-role={isPairJ ? "target" : isPairI ? "source" : undefined}
                >
                  {Array.from({ length: count }, (_, s) => (
                    <div key={s} className={styles.stickInBox} />
                  ))}
                  {count > 0 ? <span className={styles.boxCount}>{count}</span> : null}
                </div>
                <span className={labelClass}>Box {idx}</span>
              </div>
            );
          })}
        </div>

        <p className={styles.stepCue} data-testid="sticks-step-cue" aria-live="polite">
          {stepLabel || "\u00a0"}
        </p>
      </div>

      <div className={styles.stats} data-testid="sticks-stats">
        <div className={styles.stat}>
          <span className={styles.statLabel}>Rule</span>
          <span className={styles.statValue} data-testid="sticks-stat-complexity">
            {mode}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Sticks</span>
          <span className={styles.statValue} data-testid="sticks-stat-placed">
            {placed} / {target}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Steps</span>
          <span className={styles.statValue} data-testid="sticks-stat-work">
            {target}
          </span>
        </div>
      </div>

      <div className={styles.controls}>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>Rule</span>
          <select
            className={styles.select}
            value={mode}
            onChange={(e) => onModeChange(e.target.value as ComplexityMode)}
            data-testid="sticks-complexity-select"
            aria-label="Complexity rule"
            title={MODE_OPTIONS.find((o) => o.value === mode)?.title}
          >
            {MODE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value} title={opt.title}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.fieldLabel}>n</span>
          <div className={styles.sliderRow}>
            <input
              className={styles.slider}
              type="range"
              min={nMin}
              max={nMax}
              step={1}
              value={n}
              onChange={(e) => onNChange(Number(e.target.value))}
              data-testid="sticks-n-slider"
              aria-label="Problem size n"
            />
            <span className={styles.sliderValue} data-testid="sticks-n-value">
              n = {n}
            </span>
          </div>
        </label>

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.primaryBtn}
            onClick={putNextStick}
            disabled={finished}
            data-testid="sticks-primary-btn"
            data-track="sticks_boxes.put_next"
          >
            {finished ? "Finished!" : "Put Next Stick"}
          </button>
          <button
            type="button"
            className={styles.resetBtn}
            onClick={() => resetProgress(n, mode)}
            data-testid="sticks-reset-btn"
            data-track="sticks_boxes.reset"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
