import { useRef, useState, type PointerEvent } from "react";
import { missionComplete, requiredTargets, validatePlacement, type GrowthMission } from "./growthMission";
import styles from "./GrowthGame.module.css";

export default function GrowthGame({
  mission,
  onProgress,
  initialFilled = [],
}: {
  mission: GrowthMission;
  initialFilled?: readonly string[];
  onProgress: (filled: string[], finished: boolean) => void;
}) {
  const [filled, setFilled] = useState<string[]>(() => [...initialFilled]);
  const [armed, setArmed] = useState(false);
  const [feedback, setFeedback] = useState("Drag a stick to a box, or tap to place it.");
  const [dragPoint, setDragPoint] = useState<{ x: number; y: number } | null>(null);
  const [hoverTarget, setHoverTarget] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const gestureRef = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const suppressNextClick = useRef(false);
  const completed = missionComplete(mission, filled);
  const targets = requiredTargets(mission);

  function place(target: string) {
    if (completed) return;
    const verdict = validatePlacement(mission, filled, target);
    setArmed(false);
    if (verdict === "duplicate") {
      setFeedback("Already filled. Pick an empty space.");
      return;
    }
    if (verdict === "not-allowed") {
      setFeedback(mission.mode === "O(1)" ? "Only Box 1 needs a stick." : "That space isn't part of this task.");
      return;
    }
    const next = [...filled, target];
    const done = missionComplete(mission, next);
    setFilled(next);
    onProgress(next, done);
    setFeedback(done
      ? "Finished! See the graph."
      : `${next.length} stick${next.length === 1 ? "" : "s"} placed.`);
  }

  // Pointer events work on touchscreens as well as mice; HTML5 drag/drop does not.
  // The stick captures the pointer, while elementFromPoint identifies the real
  // drop zone underneath. Clicking/tapping remains available for accessibility.
  function targetAt(x: number, y: number): string | null {
    const element = document.elementFromPoint(x, y)?.closest("[data-v2-drop-target]") as HTMLElement | null;
    if (!element || !rootRef.current?.contains(element)) return null;
    return element.dataset.v2DropTarget || null;
  }

  function pointerDown(event: PointerEvent<HTMLButtonElement>) {
    if (event.button !== 0 || completed) return;
    gestureRef.current = { x: event.clientX, y: event.clientY, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function pointerMove(event: PointerEvent<HTMLButtonElement>) {
    const gesture = gestureRef.current;
    if (!gesture) return;
    if (!gesture.moved && Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) <= 6) return;
    gesture.moved = true;
    setDragPoint({ x: event.clientX, y: event.clientY });
    setHoverTarget(targetAt(event.clientX, event.clientY));
  }

  function pointerUp(event: PointerEvent<HTMLButtonElement>) {
    const gesture = gestureRef.current;
    gestureRef.current = null;
    if (!gesture) return;
    if (gesture.moved) {
      suppressNextClick.current = true;
      const target = targetAt(event.clientX, event.clientY);
      if (target) place(target);
      else setFeedback("Drop the stick into an empty box.");
      setDragPoint(null);
      setHoverTarget(null);
      setArmed(false);
    }
  }

  function pointerCancel() {
    gestureRef.current = null;
    setDragPoint(null);
    setHoverTarget(null);
    setArmed(false);
  }

  function targetButton(target: string, label: string) {
    const isFilled = filled.includes(target);
    return (
      <button
        key={target}
        type="button"
        className={isFilled ? styles.filled : hoverTarget === target ? styles.hoverTarget : styles.target}
        data-testid={`v2-target-${target}`}
        data-filled={isFilled ? "true" : "false"}
        data-v2-drop-target={target}
        aria-label={`${label}, ${isFilled ? "filled" : "empty"}`}
        aria-pressed={isFilled}
        onClick={() => armed ? place(target) : setFeedback("Pick up a stick first, then tap the target. You can also drag the stick here.")}

      >
        <span className={styles.targetLabel}>{label}</span>
        <span className={styles.targetSymbol} aria-hidden="true">{isFilled ? "┃" : "+"}</span>
      </button>
    );
  }

  return (
    <div ref={rootRef} className={styles.root} role="group" aria-label="Drag-and-drop growth game"
      data-testid="v2-growth-game" data-mission={mission.id} data-placed={filled.length}
      data-complete={completed ? "true" : "false"}>
      <div className={styles.toolRow}>
        <button
          className={armed ? styles.stickActive : styles.stick}
          type="button"
          disabled={completed}
          onPointerDown={pointerDown}
          onPointerMove={pointerMove}
          onPointerUp={pointerUp}
          onPointerCancel={pointerCancel}
          data-testid="v2-stick"
          aria-pressed={armed}
          onClick={() => {
            if (suppressNextClick.current) { suppressNextClick.current = false; return; }
            setArmed(true);
          }}
        >
          <span aria-hidden="true" className={styles.stickIcon}>┃</span>
          {armed ? "Stick selected" : "Pick up a stick"}
        </button>
        <div className={styles.counter}>
          <span>Work done</span>
          <strong data-testid="v2-live-work">{filled.length} step{filled.length === 1 ? "" : "s"}</strong>
        </div>
      </div>

      {dragPoint ? (
        <div className={styles.dragGhost} aria-hidden="true"
          style={{ left: dragPoint.x, top: dragPoint.y }}>┃</div>
      ) : null}
      {mission.mode === "O(n²)" ? (
        <div className={styles.pairBoard} aria-label="Ordered-pair board">
          <p>Each tile represents one pair of boxes. Directions count separately.</p>
          <div className={styles.pairGrid} style={{ gridTemplateColumns: `repeat(${mission.n}, minmax(0, 1fr))` }}>
            {targets.map((target) => {
              const parts = target.split(":");
              return targetButton(target, `${Number(parts[1]) + 1} → ${Number(parts[2]) + 1}`);
            })}
          </div>
        </div>
      ) : (
        <div className={styles.boxBoard} aria-label="Boxes">
          {Array.from({ length: mission.n }, (_, i) => targetButton(`box:${i}`, `Box ${i + 1}`))}
        </div>
      )}

      <p className={styles.feedback} role="status" aria-live="polite" data-testid="v2-game-feedback">{feedback}</p>
      <details className={styles.hint}><summary>Need a hint?</summary><p>{mission.actionHint}</p></details>
      <button
        type="button" className={styles.reset} data-testid="v2-restart"
        onClick={() => { setFilled([]); setArmed(false); setFeedback("Board reset. Pick up a stick and try the mission again."); onProgress([], false); }}
      >Start this board over</button>
    </div>
  );
}
