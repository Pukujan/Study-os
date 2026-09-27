import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import FractionBar from "./FractionBar";
import BoxIndex from "./BoxIndex";
import Frame from "./Frame";
import MermaidDiagram from "./MermaidDiagram";
import LessonMap from "./LessonMap";
import CodeTree from "./CodeTree";
import GrowthTable from "./GrowthTable";
import GrowthCurve from "./GrowthCurve";
import GrowthWorkers from "./GrowthWorkers";

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

  it("GrowthTable renders n columns, labels and bars", () => {
    const frame = {
      type: "growth_table" as const,
      n_values: [2, 4, 8],
      series: { label: "O(n)", values: [2, 4, 8] },
      caption: "linear",
    };
    const html = renderToStaticMarkup(<GrowthTable frame={frame} />);
    expect(html).toContain("growth-table");
    expect(html).toContain("O(n)");
    expect(html).toContain("growth-table-bar");
    expect(html).toContain('aria-label="Growth table for n = 2, 4, 8; O(n): 2, 4, 8"');
  });

  it("Frame dispatches growth_table frames", () => {
    const frame = {
      type: "growth_table" as const,
      n_values: [16],
      series_multi: [
        { label: "O(1)", values: [1] },
        { label: "O(n²)", values: [256] },
      ],
      caption: "Side-by-side at n = 16.",
    };
    const html = renderToStaticMarkup(<Frame frame={frame} />);
    expect(html).toContain("O(n²)");
    expect(html).toContain("256");
    expect(html).toContain("Side-by-side at n = 16.");
    expect(html).toContain("teach-render-box");
    expect(html).toContain('data-teach-render="growth_table"');
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

  it("LessonMap makes visited steps revisitable when a handler is given", () => {
    const steps = [
      { id: "ready", label: "Ready" },
      { id: "pos", label: "Position" },
      { id: "idx", label: "Index" },
    ];
    const onSelect = () => {};
    const html = renderToStaticMarkup(
      <LessonMap steps={steps} currentIndex={2} completedIds={["ready", "pos"]} selectableCount={2} onSelect={onSelect} />,
    );
    expect(html).toContain("player.revisit-0");
    expect(html).toContain("player.revisit-1");
    expect(html).not.toContain("player.revisit-2");
  });

  it("LessonMap keeps visited chips inert without a handler", () => {
    const steps = [
      { id: "ready", label: "Ready" },
      { id: "pos", label: "Position" },
    ];
    const html = renderToStaticMarkup(<LessonMap steps={steps} currentIndex={1} completedIds={["ready"]} />);
    expect(html).not.toContain("player.revisit-0");
    expect(html).not.toContain("<button");
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


  it("GrowthWorkers draws hikers and n labels", () => {
    const frame = {
      type: "growth_workers" as const,
      n_values: [2, 4, 8, 16],
      role_label: "workers",
      caption: "boxes grow",
    };
    const html = renderToStaticMarkup(<GrowthWorkers frame={frame} />);
    expect(html).toContain("growth-workers");
    expect(html).toContain("n=2");
    expect(html).toContain("n=16");
    expect(html).toContain("workers carrying boxes");
  });

  it("Frame dispatches growth_workers and growth_curve", () => {
    const workers = renderToStaticMarkup(
      <Frame frame={{ type: "growth_workers", n_values: [2, 4], role_label: "workers" }} />,
    );
    expect(workers).toContain("teach-render-box");
    expect(workers).toContain('data-teach-render="growth_workers"');
    expect(workers).toContain("growth-workers");
    const curve = renderToStaticMarkup(
      <Frame
        frame={{
          type: "growth_curve",
          n_values: [2, 4],
          series_multi: [
            { label: "slow", values: [1, 2] },
            { label: "fast", values: [4, 16] },
          ],
        }}
      />,
    );
    expect(curve).toContain("teach-render-box");
    expect(curve).toContain('data-teach-render="growth_curve"');
    expect(curve).toContain("growth-curve");
  });

  it("GrowthCurve emphasises the class named by highlight_label (#161)", () => {
    const fourClass = [
      { label: "O(1)", values: [1, 1, 1, 1] },
      { label: "O(log n)", values: [1, 2, 3, 4] },
      { label: "O(n)", values: [2, 4, 8, 16] },
      { label: "O(n²)", values: [4, 16, 64, 256] },
    ];
    const highlighted = renderToStaticMarkup(
      <Frame
        frame={{
          type: "growth_curve",
          n_values: [2, 4, 8, 16],
          series_multi: fourClass,
          highlight_label: "O(n²)",
        }}
      />,
    );
    expect(highlighted).toContain("highlighting O(n²)");
    // Only the taught class keeps full opacity on the plot.
    expect(highlighted.match(/opacity="0.35"/g)?.length).toBe(3);
    expect(highlighted).toContain('stroke-width="3.5"');

    const unhighlighted = renderToStaticMarkup(
      <Frame
        frame={{ type: "growth_curve", n_values: [2, 4, 8, 16], series_multi: fourClass }}
      />,
    );
    expect(unhighlighted).not.toContain("highlighting");
    expect(unhighlighted).not.toContain('opacity="0.35"');
    expect(unhighlighted).not.toContain('stroke-width="3.5"');
  });

  it("GrowthTable empty series hides scoreboard and shows a helpful hint (#178)", () => {
    const html = renderToStaticMarkup(
      <GrowthTable frame={{ type: "growth_table", n_values: [2, 4, 8, 16] }} />,
    );
    expect(html).toContain('data-testid="growth-table-empty"');
    expect(html).not.toContain("growth-scoreboard-chips");
    expect(html).not.toContain("Counts arrive in the next steps.");
    expect(html).toContain("Estimate how the step count changes as n grows.");
    expect(html).toContain("n = 2, 4, 8, 16");
  });

  it("GrowthTable empty_hint overrides the default probe line (#178)", () => {
    const html = renderToStaticMarkup(
      <GrowthTable
        frame={{
          type: "growth_table",
          n_values: [4, 1000],
          empty_hint: "Reading a[0] is one lookup. Does that stay 1 when n grows?",
        }}
      />,
    );
    expect(html).toContain("Reading a[0] is one lookup");
    expect(html).not.toContain("Counts arrive");
  });

  it("GrowthCurve shows textbook end-of-line labels in curve color, no swatch legend (#179)", () => {
    const fourClass = [
      { label: "O(1)", values: [1, 1, 1, 1] },
      { label: "O(log n)", values: [1, 2, 3, 4] },
      { label: "O(n)", values: [2, 4, 8, 16] },
      { label: "O(n²)", values: [4, 16, 64, 256] },
    ];
    const html = renderToStaticMarkup(
      <GrowthCurve frame={{ type: "growth_curve", n_values: [2, 4, 8, 16], series_multi: fourClass }} />,
    );
    // On-plot end labels are enough — drop the separate swatch legend that made learners hunt.
    expect(html).not.toContain("growth-curve-legend");
    expect(html).not.toContain("growth-curve-legend-swatch");
    expect(html).toContain('data-series-label="O(1)"');
    expect(html).toContain('data-series-label="O(log n)"');
    expect(html).toContain('data-series-label="O(n)"');
    expect(html).toContain('data-series-label="O(n²)"');
    expect(html).toContain("growth-curve-end-label");
    // Clean axes (textbook Input size / Time).
    expect(html).toContain("growth-curve-axis-x");
    expect(html).toContain("growth-curve-axis-y");
    expect(html).toContain("Input size");
    expect(html).toContain("Time");
    // Labels use the same token colors as their curves (O(1)=chart-3, log=chart-4, n=chart-1, n²=chart-2).
    expect(html).toMatch(/data-series-label="O\(1\)"[^>]*fill="var\(--chart-3/);
    expect(html).toMatch(/data-series-label="O\(log n\)"[^>]*fill="var\(--chart-4/);
    expect(html).toMatch(/data-series-label="O\(n\)"[^>]*fill="var\(--chart-1/);
    expect(html).toMatch(/data-series-label="O\(n²\)"[^>]*fill="var\(--chart-2/);
  });

  it("Frame mounts growth frames inside TeachRenderBox island", () => {
    const html = renderToStaticMarkup(
      <Frame
        frame={{
          type: "growth_table",
          n_values: [2, 4, 8, 16],
          series: { label: "O(n)", values: [2, 4, 8, 16] },
        }}
      />,
    );
    expect(html).toContain('data-testid="teach-render-box"');
    expect(html).toContain('data-teach-render="growth_table"');
    expect(html).toContain("O(n)");
  });

});
