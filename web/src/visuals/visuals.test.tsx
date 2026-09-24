import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import FractionBar from "./FractionBar";
import BoxIndex from "./BoxIndex";
import Frame from "./Frame";

describe("visuals", () => {
  it("FractionBar renders the right aria-label and shaded parts", () => {
    const frame = { type: "fraction_bar" as const, bars: [{ parts: 4, shaded: 3, label: "3/4" }] };
    const html = renderToStaticMarkup(<FractionBar frame={frame} />);
    expect(html).toContain('aria-label="Bar cut into 4 equal parts, 3 shaded, labeled 3/4"');
    const shaded = (html.match(/fill="var\(--primary\)"/g) || []).length;
    expect(shaded).toBe(3);
  });

  it("BoxIndex renders the right aria-label and box", () => {
    const frame = { type: "box_index" as const, array: [4, 7, 2, 6], show_positions: true, show_indices: true, box: { start: 1, k: 2 }, arrows: [{ at: 2, label: "p", row: "positions" as const }], sum_label: "sum = 9" };
    const html = renderToStaticMarkup(<BoxIndex frame={frame} />);
    expect(html).toContain('aria-label="Array [4, 7, 2, 6]; box covers indices 1 through 2; arrows at p on positions; sum sum = 9"');
  });

  it("Frame dispatches by type and includes an aria-label", () => {
    const frame = { type: "fraction_bar" as const, bars: [{ parts: 2, shaded: 1 }] };
    const html = renderToStaticMarkup(<Frame frame={frame} />);
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Bar cut into 2 equal parts, 1 shaded"');
  });
});
