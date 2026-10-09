import { useState, type DragEvent } from "react";
import { missionComplete, requiredTargets, validatePlacement, type GrowthMission } from "./growthMission";
import styles from "./GrowthGame.module.css";

export default function GrowthGame({
  mission,
  onProgress,
}: {
  mission: GrowthMission;
  onProgress: (count: number, finished: boolean) => void;
}) {
  const [filled, setFilled] = useState<string[]>([]);
  const [armed, setArmed] = useState(false);
  const [feedback, setFeedback] = useState("Pick up a stick, then drop or tap a target.");
  const completed = missionComplete(mission, filled);
  const targets = requiredTargets(mission);

  function place(target: string) {
    if (completed) return;
    const verdict = validatePlacement(mission, filled, target);
    setArmed(false);
    if (verdict === "duplicate") {
      setFeedback("Already filled! Look for a different empty space.");
      return;
    }
    if (verdict === "not-allowed") {
      setFeedback("That box is not part of the computer's rule. Re-read the mission and try again.");
      return;
    }
    const next = [...filled, target];
    const done = missionComplete(mission, next);
    setFilled(next);
    onProgress(next.length, done);
    setFeedback(done
      ? "Nice work. Your actions completed this rule! Notice the finished graph beside the board."
      : "Correct placement. Watch the graph rise as the work counter increases.");
  }

  function drop(event: DragEvent<HTMLButtonElement>, target: string) {
    event.preventDefault();
    if (event.dataTransfer.getData("text/plain") !== "study-os-stick") return;
    place(target);
  }

  function targetButton(target: string, label: string) {
    const isFilled = filled.includes(target);
    return (
      <button
        key={target}
        type="button"
        className={isFilled ? styles.filled : styles.target}
        data-testid={`v2-target-${target}`}
        data-filled={isFilled ? "true" : "false"}
        aria-label={`${label}, ${isFilled ? "filled" : "empty"}`}
        aria-pressed={isFilled}
        onClick={() => armed ? place(target) : setFeedback("Pick up a stick first, then tap the target. You can also drag the stick here.")}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => drop(event, target)}
      >
        <span className={styles.targetLabel}>{label}</span>
        <span className={styles.targetSymbol} aria-hidden="true">{isFilled ? "┃" : "+"}</span>
      </button>
    );
  }

  return (
    <div className={styles.root} role="group" aria-label="Drag-and-drop growth game"
      data-testid="v2-growth-game" data-mission={mission.id} data-placed={filled.length}
      data-complete={completed ? "true" : "false"}>
      <div className={styles.toolRow}>
        <button
          className={armed ? styles.stickActive : styles.stick}
          type="button"
          draggable={!completed}
          disabled={completed}
          data-testid="v2-stick"
          aria-pressed={armed}
          onClick={() => setArmed(true)}
          onDragStart={(event) => {
            event.dataTransfer.setData("text/plain", "study-os-stick");
            event.dataTransfer.effectAllowed = "copy";
            setArmed(true);
          }}
          onDragEnd={() => setArmed(false)}
        >
          <span aria-hidden="true" className={styles.stickIcon}>┃</span>
          {armed ? "Stick selected" : "Pick up a stick"}
        </button>
        <div className={styles.counter}>
          <span>Work done</span>
          <strong data-testid="v2-live-work">{filled.length} step{filled.length === 1 ? "" : "s"}</strong>
        </div>
      </div>

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
      <p className={styles.hint}>{mission.actionHint}</p>
      <button
        type="button" className={styles.reset} data-testid="v2-restart"
        onClick={() => { setFilled([]); setArmed(false); setFeedback("Board reset. Pick up a stick and try the mission again."); onProgress(0, false); }}
      >Start this board over</button>
    </div>
  );
}
