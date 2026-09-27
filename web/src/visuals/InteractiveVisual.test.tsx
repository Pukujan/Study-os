import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import InteractiveVisual from "./InteractiveVisual";
import type { InteractiveVisualFrame } from "../api";

describe("InteractiveVisual", () => {
  it("renders match_curves panels", () => {
    const frame: InteractiveVisualFrame = {
      type: "interactive_visual",
      exercise_kind: "match_curves",
      prompt: "Match",
      n_values: [1, 2, 4, 8, 16],
      panels: [
        { id: "A", shape: "flat" },
        { id: "B", shape: "linear" },
        { id: "C", shape: "steep" },
      ],
      labels: ["O(1)", "O(n)", "O(n²)"],
    };
    const html = renderToStaticMarkup(<InteractiveVisual frame={frame} />);
    expect(html).toContain('data-exercise-kind="match_curves"');
    expect(html).toContain('data-testid="iv-panel-A"');
    expect(html).not.toContain("<ol");
  });
});
