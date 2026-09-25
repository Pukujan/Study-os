import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import FractionBar from "./FractionBar";
import BoxIndex from "./BoxIndex";
import Frame from "./Frame";
import MermaidDiagram from "./MermaidDiagram";
import LessonMap from "./LessonMap";
import CodeTree from "./CodeTree";

describe("visuals", () => {
  it("FractionBar renders the right aria-label and shaded parts", () => {
    const frame = { type: "fraction_bar" as const, bars: [{ parts: 4, shaded: 3, label: "3/4" }] };
    const html = renderToStaticMarkup(<FractionBar frame={frame} />);
    expect(html).toContain('aria-label="Bar cut into 4 equal parts, 3 shaded, labeled 3/4"');
    const shaded = (html.match(/fill="var\(--primary\)"/g) || []).length;
    expect(shaded).toBe(3);
  });

  it("BoxIndex renders the right aria-label and box", () => {
    const frame = {
      type: "box_index" as const,
      array: [4, 7, 2, 6],
      show_positions: true,
      show_indices: true,
      box: { start: 1, k: 2, brace_label: "k = 2" },
      arrows: [{ at: 2, label: "p", row: "positions" as const, dir: "down" as const }],
      sum_label: "sum = 9",
    };
    const html = renderToStaticMarkup(<BoxIndex frame={frame} />);
    expect(html).toContain('aria-label="Array [4, 7, 2, 6]; box covers indices 1 through 2; brace label k = 2; arrows p at 2 on positions down; sum sum = 9"');
  });

  it("BoxIndex draws a brace and arrow labels", () => {
    const frame = {
      type: "box_index" as const,
      array: [4, 7, 2],
      show_positions: false,
      show_indices: true,
      box: { start: 0, k: 2, brace_label: "box" },
      arrows: [{ at: 1, label: "↑", row: "numbers" as const, dir: "up" as const }],
    };
    const html = renderToStaticMarkup(<BoxIndex frame={frame} />);
    expect(html).toContain("box");
    expect(html).toContain("└");
    expect(html).toContain("↑");
  });

  it("BoxIndex draws circles around circled indices", () => {
    const frame = {
      type: "box_index" as const,
      array: [4, 7, 2],
      show_positions: false,
      show_indices: true,
      box: null,
      circles: [1],
    };
    const html = renderToStaticMarkup(<BoxIndex frame={frame} />);
    expect(html).toContain("ellipse");
    expect(html).toContain("Array [4, 7, 2]; circled indices 1");
  });

  it("Frame dispatches by type and includes an aria-label", () => {
    const frame = { type: "fraction_bar" as const, bars: [{ parts: 2, shaded: 1 }] };
    const html = renderToStaticMarkup(<Frame frame={frame} />);
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Bar cut into 2 equal parts, 1 shaded"');
  });

  it("MermaidDiagram renders a simple source without crashing", () => {
    const html = renderToStaticMarkup(
      <MermaidDiagram source="flowchart TD\n  A[Hello] --> B[World]" revealedNodes={["A"]} />,
    );
    expect(html).toContain("Loading diagram");
    expect(html).toContain("role=\"img\"");
  });

  it("LessonMap renders compact step chips", () => {
    const steps = [
      { id: "ready", label: "Ready" },
      { id: "pos", label: "Position" },
      { id: "idx", label: "Index" },
    ];
    const html = renderToStaticMarkup(<LessonMap steps={steps} currentIndex={1} completedIds={["ready"]} />);
    expect(html).toContain("Lesson progress map");
    expect(html).toContain("lesson-map-chips");
    expect(html).toContain("is-current");
    expect(html).toContain("Position");
  });

  it("CodeTree highlights lines and underlines ranges", () => {
    const frame = {
      type: "code_tree" as const,
      lines: ["S = []", "for i, num in enumerate(a):", "    S.append(num)"],
      highlight: [1],
      underlines: [{ line: 2, span: [4, 16] as [number, number], label: "same expression" }],
    };
    const html = renderToStaticMarkup(<CodeTree frame={frame} />);
    expect(html).toContain("code-tree");
    expect(html).toContain("S.append(num");
    expect(html).toContain("same expression");
  });
});
