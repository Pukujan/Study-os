/**
 * Interactive sticks-and-boxes Big O teach visual (#185 / #191).
 *
 * Learner acts as the computer: click target box or Put Next Stick / compare-next /
 * Finished / Reset under O(1) / O(n) / O(n²) rules. UX class grounded on the
 * user-validated Gemini exemplar (see content/teach-visuals/_research/big-o/sticks-boxes-gemini-exemplar/).
 */
import { useMemo, useState } from "react";
import type { SticksBoxesComplexityFrame } from "../api";
import styles from "./SticksBoxesComplexity.module.css";
import cssText from "./SticksBoxesComplexity.module.css?inline";

export type ComplexityMode = "O(1)" | "O(n)" | "O(n²)";

const MODE_ORDER: ComplexityMode[] = ["O(1)", "O(n)", "O(n²)"];

const MODE_OPTIONS: { value: ComplexityMode; label: string }[] = [
  { value: "O(1)", label: "O(1) Constant — Put 1 stick in first box" },
  { value: "O(n)", label: "O(n) Linear — Put 1 stick in each box" },
  { value: "O(n²)", label: "O(n²) Quadratic — Cross-pair every box with every box" },
];

/** Default problem size shown in the interactive (lesson frames may override). */
export const DEFAULT_N = 3;
const DEFAULT_N_MIN = 2;
const DEFAULT_N_MAX = 8;
/** Suggested larger n for feeling O(n) growth after finishing at the default. */
export const COMPARE_N_HINT = 5;

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

/** Next complexity to compare after finishing `mode`, or null when all done. */
export function nextCompareMode(mode: ComplexityMode): ComplexityMode | null {
  const idx = MODE_ORDER.indexOf(mode);
  if (idx < 0 || idx >= MODE_ORDER.length - 1) return null;
  return MODE_ORDER[idx + 1];
}

export function compareCtaLabel(next: ComplexityMode): string {
  return `Let's compare that to ${next}`;
}

export type PrimaryAction =
  | { kind: "put" }
  | { kind: "try_n"; n: number }
  | { kind: "compare"; mode: ComplexityMode }
  | { kind: "finished" };

/**
 * Primary CTA after (or during) play:
 * - not finished → Put Next Stick
 * - finished O(n) with n < COMPARE_N_HINT → try larger n (keep O(n))
 * - finished with a next mode → compare CTA
 * - else Finished!
 */
export function resolvePrimaryAction(
  mode: ComplexityMode,
  n: number,
  finished: boolean,
  compareN: number = COMPARE_N_HINT,
): PrimaryAction {
  if (!finished) return { kind: "put" };
  if (mode === "O(n)" && n < compareN) return { kind: "try_n", n: compareN };
  const next = nextCompareMode(mode);
  if (next) return { kind: "compare", mode: next };
  return { kind: "finished" };
}

export function primaryActionLabel(action: PrimaryAction): string {
  if (action.kind === "put") return "Put Next Stick";
  if (action.kind === "try_n") return `Try the same rule at n = ${action.n}`;
  if (action.kind === "compare") return compareCtaLabel(action.mode);
  return "Finished!";
}

/** Heat / stress tier from Total Work (ops): calm → warm → melting. */
export function workHeatTier(ops: number): "calm" | "warm" | "melting" {
  if (ops <= 1) return "calm";
  if (ops <= 8) return "warm";
  return "melting";
}

const HEAT_COPY: Record<"calm" | "warm" | "melting", { emoji: string; label: string }> = {
  calm: { emoji: "😌", label: "Calm — little work" },
  warm: { emoji: "😅", label: "Warming up — work grows with n" },
  melting: { emoji: "🫠", label: "Melting — work explodes" },
};

export function describeSticksBoxesComplexity(frame: SticksBoxesComplexityFrame): string {
  const mode = frame.initial_complexity || "O(1)";
  const n = frame.initial_n ?? DEFAULT_N;
  return frame.caption || `Sticks and boxes for ${mode} with problem size n = ${n}`;
}

function emptyCounts(n: number): number[] {
  return Array.from({ length: n }, () => 0);
}

export default function SticksBoxesComplexity({ frame }: { frame: SticksBoxesComplexityFrame }) {
  const nMin = frame.n_min ?? DEFAULT_N_MIN;
  const nMax = frame.n_max ?? DEFAULT_N_MAX;
  const startN = clamp(frame.initial_n ?? DEFAULT_N, nMin, nMax);
  const startMode = (frame.initial_complexity || "O(1)") as ComplexityMode;

  const [mode, setMode] = useState<ComplexityMode>(startMode);
  const [n, setN] = useState(startN);
  const [counts, setCounts] = useState<number[]>(() => emptyCounts(startN));
  const [placed, setPlaced] = useState(0);

  const target = targetSticks(mode, n);
  const finished = placed >= target;
  const nextDest = destinationBox(mode, n, placed);
  const pair = currentPair(mode, n, placed);
  const primary = resolvePrimaryAction(mode, n, finished);
  const heat = workHeatTier(target);
  const heatMeta = HEAT_COPY[heat];

  const stepLabel = useMemo(() => {
    if (mode !== "O(n²)" || finished || !pair) return null;
    return `Step ${placed + 1}: Cross-Pairing Box ${pair.i} × Box ${pair.j}`;
  }, [mode, finished, pair, placed]);

  const growthCue = useMemo(() => {
    if (mode === "O(n)" && !finished) {
      return `O(n): Total Work equals n. Slide n (try ${Math.min(startN, COMPARE_N_HINT)} then ${COMPARE_N_HINT}) and watch the computer's work grow.`;
    }
    if (mode === "O(n)" && finished && n < COMPARE_N_HINT) {
      return `Finished at n = ${n} → Total Work ${target}. Try n = ${COMPARE_N_HINT} next — work should become ${COMPARE_N_HINT}.`;
    }
    if (mode === "O(n²)" && !finished) {
      return `O(n²): Total Work is n × n. Even a few more boxes means a lot more sticks (work).`;
    }
    return null;
  }, [mode, finished, n, target, startN]);

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

  function onBoxActivate(idx: number) {
    if (finished) return;
    if (nextDest !== idx) return;
    putNextStick();
  }

  function onPrimaryAction() {
    if (primary.kind === "put") {
      putNextStick();
      return;
    }
    if (primary.kind === "try_n") {
      onNChange(primary.n);
      return;
    }
    if (primary.kind === "compare") {
      onModeChange(primary.mode);
      return;
    }
  }

  const primaryDisabled = primary.kind === "finished";

  return (
    <div
      className={styles.root}
      data-testid="sticks-boxes-complexity"
      data-complexity={mode}
      data-n={n}
      data-placed={placed}
      data-target={target}
      data-heat={heat}
      role="group"
      aria-label={describeSticksBoxesComplexity(frame)}
    >
      <style>{cssText}</style>
      <p className={styles.intro}>
        You are the computer. Each stick is a bit of work. Put sticks into boxes under each rule and
        watch how <strong>work grows as the problem size n grows</strong>. Here <strong>n</strong> is
        how big the problem is (input size); work is the ops you place.
      </p>
      <p className={styles.scaleNote} data-testid="sticks-scale-note">
        Example only: if the computer had to do this for <strong>n = 3</strong> vs{" "}
        <strong>n = 1 billion</strong>, we would not draw a billion boxes — but the same rule still
        says how the work explodes.
      </p>

      <div className={styles.stageRow}>
        <div className={styles.stage}>
          <div className={styles.dispenser}>
            <div className={styles.dispenserTray} aria-hidden="true">
              {!finished ? <div className={styles.dispenserStick} /> : null}
            </div>
            <span className={styles.dispenserLabel}>Stick Dispenser</span>
          </div>

          <div className={styles.boxesRow}>
            {counts.map((count, idx) => {
              const isDest = !finished && nextDest === idx;
              const isPairI = Boolean(pair && pair.i === idx);
              const isPairJ = Boolean(pair && pair.j === idx && pair.i !== pair.j);
              const boxClass = [
                styles.box,
                isDest ? styles.boxClickable : "",
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
                  <button
                    type="button"
                    className={boxClass}
                    data-testid={`sticks-box-${idx}`}
                    data-active={isDest || isPairI ? "true" : "false"}
                    data-pair-role={isPairJ ? "target" : isPairI ? "source" : undefined}
                    data-clickable={isDest ? "true" : "false"}
                    aria-label={
                      isDest
                        ? `Place stick in Box ${idx}`
                        : `Box ${idx}${count ? `, ${count} sticks` : ""}`
                    }
                    disabled={!isDest}
                    onClick={() => onBoxActivate(idx)}
                  >
                    {Array.from({ length: count }, (_, s) => (
                      <div key={s} className={styles.stickInBox} />
                    ))}
                    {count > 0 ? <span className={styles.boxCount}>{count}</span> : null}
                  </button>
                  <span className={labelClass}>Box {idx}</span>
                </div>
              );
            })}
          </div>

          <p className={styles.stepCue} data-testid="sticks-step-cue" aria-live="polite">
            {stepLabel || "\u00a0"}
          </p>
          {growthCue ? (
            <p className={styles.growthCue} data-testid="sticks-growth-cue" aria-live="polite">
              {growthCue}
            </p>
          ) : null}
        </div>

        <aside
          className={`${styles.heatPanel} ${styles[`heat_${heat}`]}`}
          data-testid="sticks-heat-panel"
          data-heat={heat}
          aria-live="polite"
          aria-label={`Computer stress: ${heatMeta.label}. Total work ${target} ops.`}
        >
          <div className={styles.heatFace} aria-hidden="true">
            <span className={styles.heatEmoji}>{heatMeta.emoji}</span>
            <svg className={styles.heatGauge} viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">
              <circle cx="24" cy="24" r="20" className={styles.heatGaugeTrack} />
              <circle
                cx="24"
                cy="24"
                r="20"
                className={styles.heatGaugeFill}
                style={{
                  strokeDasharray: `${Math.min(1, target / Math.max(n * n, 1)) * 125.6} 125.6`,
                }}
              />
            </svg>
          </div>
          <span className={styles.heatTitle}>As work climbs</span>
          <span className={styles.heatLabel} data-testid="sticks-heat-label">
            {heatMeta.label}
          </span>
          <span className={styles.heatOps} data-testid="sticks-heat-ops">
            {target} ops
          </span>
        </aside>
      </div>

      <div className={styles.stats} data-testid="sticks-stats">
        <div className={styles.stat}>
          <span className={styles.statLabel}>Complexity</span>
          <span className={styles.statValue} data-testid="sticks-stat-complexity">
            {mode}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Sticks Placed</span>
          <span className={styles.statValue} data-testid="sticks-stat-placed">
            {placed} / {target}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total Work</span>
          <span className={styles.statValue} data-testid="sticks-stat-work">
            {target} ops
          </span>
        </div>
      </div>

      <div className={styles.controls}>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>Algorithm Complexity</span>
          <select
            className={styles.select}
            value={mode}
            onChange={(e) => onModeChange(e.target.value as ComplexityMode)}
            data-testid="sticks-complexity-select"
            aria-label="Algorithm Complexity"
          >
            {MODE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span className={styles.fieldLabel}>How big the problem is (n)</span>
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
              aria-label="How big the problem is (n)"
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
            onClick={onPrimaryAction}
            disabled={primaryDisabled}
            data-testid="sticks-primary-btn"
            data-track={
              primary.kind === "put"
                ? "sticks_boxes.put_next"
                : primary.kind === "try_n"
                  ? "sticks_boxes.try_n"
                  : primary.kind === "compare"
                    ? "sticks_boxes.compare_next"
                    : "sticks_boxes.finished"
            }
          >
            {primaryActionLabel(primary)}
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
