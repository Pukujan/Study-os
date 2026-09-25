import MermaidDiagram from "./MermaidDiagram";

export type LessonMapStep = {
  id: string;
  label: string;
};

function slugId(label: string, fallback: string): string {
  const slug = label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || fallback;
}

export function getLessonSteps(lesson_id: string, total_steps: number): LessonMapStep[] {
  // Labels must be Mermaid-safe when quoted; avoid raw [] in unquoted node text.
  const known: Record<string, string[]> = {
    "sliding-window-box": ["Ready", "Position", "Index", "Box k", "Move i", "sum i"],
  };
  const labels = known[lesson_id];
  if (labels) {
    return labels.slice(0, total_steps).map((label, i) => ({ id: slugId(label, `s${i}`), label }));
  }
  return Array.from({ length: total_steps }, (_, i) => ({ id: `step-${i}`, label: `Step ${i + 1}` }));
}

function buildSource(steps: LessonMapStep[]): string {
  // Quote node labels so characters like [] never break the Mermaid parser.
  let source = "flowchart TD\n";
  steps.forEach((step, i) => {
    const safe = step.label.replace(/"/g, "#quot;");
    source += `  ${step.id}["${safe}"]\n`;
    if (i > 0) {
      source += `  ${steps[i - 1].id} --> ${step.id}\n`;
    }
  });
  return source;
}

type LessonMapProps = {
  steps: LessonMapStep[];
  currentIndex: number;
  completedIds?: string[];
};

export default function LessonMap({ steps, currentIndex, completedIds }: LessonMapProps) {
  const revealedSet = new Set<string>();
  for (let i = 0; i <= currentIndex && i < steps.length; i++) {
    revealedSet.add(steps[i].id);
  }
  (completedIds || []).forEach((id) => revealedSet.add(id));
  const revealed = Array.from(revealedSet);
  const source = buildSource(steps);
  return (
    <div className="lesson-map" role="navigation" aria-label="Lesson progress map">
      <MermaidDiagram source={source} revealedNodes={revealed} direction="LR" zoomPan={true} caption="Lesson progress map" />
    </div>
  );
}
