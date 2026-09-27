import type { CSSProperties } from "react";

export type LessonMapStep = {
  id: string;
  label: string;
};

function slugId(label: string, fallback: string): string {
  const slug = label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || fallback;
}

export function getLessonSteps(lesson_id: string, total_steps: number): LessonMapStep[] {
  const known: Record<string, string[]> = {
    "sliding-window-box": ["Ready", "Position", "Index", "Box k", "Move i", "sum i"],
  };
  const labels = known[lesson_id];
  if (labels) {
    return labels.slice(0, total_steps).map((label, i) => ({ id: slugId(label, `s${i}`), label }));
  }
  return Array.from({ length: total_steps }, (_, i) => ({ id: `step-${i}`, label: `Step ${i + 1}` }));
}

type LessonMapProps = {
  steps: LessonMapStep[];
  currentIndex: number;
  completedIds?: string[];
  onSelect?: (index: number) => void;
  selectableCount?: number;
};

export default function LessonMap({ steps, currentIndex, completedIds, onSelect, selectableCount = 0 }: LessonMapProps) {
  const done = new Set(completedIds || []);
  return (
    <nav className="lesson-map lesson-map-chips" aria-label="Lesson progress map">
      <ol className="lesson-map-list">
        {steps.map((step, i) => {
          const state = i === currentIndex ? "current" : done.has(step.id) || i < currentIndex ? "done" : "todo";
          const style: CSSProperties = {};
          const revisitable = !!onSelect && i < Math.min(selectableCount, currentIndex);
          const label = (
            <>
              <span className="lesson-map-chip-index">{i + 1}</span>
              <span className="lesson-map-chip-label">{step.label}</span>
            </>
          );
          return (
            <li key={step.id} className={`lesson-map-chip is-${state}`} style={style} aria-current={state === "current" ? "step" : undefined}>
              {revisitable ? (
                <button
                  type="button"
                  className="lesson-map-chip-button"
                  onClick={() => onSelect?.(i)}
                  data-track={`player.revisit.${i}`}
                  data-testid={`player.revisit-${i}`}
                >
                  {label}
                </button>
              ) : (
                label
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
