import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import BoxIndex from "./BoxIndex";

describe("BoxIndex up-arrows vs numbers", () => {
  it("keeps up-arrow tips below the number glyphs", () => {
    const frame = {
      type: "box_index" as const,
      array: [4, 7, 2, 6, 1, 9],
      show_positions: false,
      show_indices: true,
      box: { start: 0, k: 3, brace_label: "k = 3" },
      arrows: [
        { at: 0, label: "L", row: "numbers" as const, dir: "up" as const },
        { at: 1, label: "M", row: "numbers" as const, dir: "up" as const },
        { at: 2, label: "R", row: "numbers" as const, dir: "up" as const },
      ],
    };
    const html = renderToStaticMarkup(<BoxIndex frame={frame} />);
    expect(html).toContain(">4<");
    expect(html).toContain(">7<");
    expect(html).toContain(">2<");

    // React serializes markerEnd as marker-end in SVG markup.
    const lines = [...html.matchAll(/<line\b[^>]*>/g)].filter((m) => /arrowhead-up/.test(m[0]));
    expect(lines.length).toBe(3);
    for (const line of lines) {
      const y2 = /\by2="(\d+(?:\.\d+)?)"/.exec(line[0]);
      const y1 = /\by1="(\d+(?:\.\d+)?)"/.exec(line[0]);
      expect(y2).toBeTruthy();
      expect(y1).toBeTruthy();
      const tip = Number(y2![1]);
      const start = Number(y1![1]);
      // With indices on: numbersY=64, number text at 66; tip must stay below cell (~74+).
      expect(tip).toBeGreaterThan(66);
      expect(start).toBeGreaterThan(tip);
    }
  });
});
