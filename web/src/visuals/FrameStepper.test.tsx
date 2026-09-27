import { describe, expect, it } from "vitest";
import { act } from "react";
import FrameStepper from "./FrameStepper";
import { render } from "../test-utils";

const frames = [
  { type: "fraction_bar" as const, bars: [{ parts: 2, shaded: 1 }] },
  { type: "fraction_bar" as const, bars: [{ parts: 3, shaded: 2 }] },
  { type: "fraction_bar" as const, bars: [{ parts: 4, shaded: 3 }] },
];

/** Count nodes across open shadow roots (TeachRenderBox islands). */
function queryAllDeep(root: ParentNode, selector: string): Element[] {
  const out: Element[] = [];
  root.querySelectorAll(selector).forEach((el) => out.push(el));
  root.querySelectorAll("*").forEach((el) => {
    if (el.shadowRoot) out.push(...queryAllDeep(el.shadowRoot, selector));
  });
  return out;
}

describe("FrameStepper", () => {
  it("shows one frame at a time and no controls for a single frame", () => {
    const { container, cleanup } = render(
      <FrameStepper frames={[{ type: "fraction_bar" as const, bars: [{ parts: 2, shaded: 1 }] }]} />,
    );
    const svgs = queryAllDeep(container, "svg");
    expect(svgs.length).toBe(1);
    expect(container.querySelector("button")).toBeNull();
    cleanup();
  });

  it("never autoplays and navigates with Back / Next", () => {
    const { container, cleanup } = render(<FrameStepper frames={frames} />);
    const count = container.querySelector(".frame-stepper-count");
    expect(count?.textContent).toBe("1 of 3");
    const next = container.querySelector<HTMLButtonElement>("button[aria-label='Next frame']");
    act(() => next?.click());
    expect(container.querySelector(".frame-stepper-count")?.textContent).toBe("2 of 3");
    const back = container.querySelector<HTMLButtonElement>("button[aria-label='Previous frame']");
    act(() => back?.click());
    expect(container.querySelector(".frame-stepper-count")?.textContent).toBe("1 of 3");
    cleanup();
  });

  it("survives Explain-again shrink after Next (stale index must not read .type)", () => {
    const multi = [
      { type: "growth_curve" as const, n_values: [2, 4], series_multi: [{ label: "O(1)", values: [1, 1] }] },
      { type: "growth_workers" as const, n_values: [2, 4] },
    ];
    const { container, cleanup, rerender } = render(<FrameStepper frames={multi} />);
    const next = container.querySelector<HTMLButtonElement>("button[aria-label='Next frame']");
    act(() => next?.click());
    expect(container.querySelector(".frame-stepper-count")?.textContent).toBe("2 of 2");
    // Second Explain again often collapses back to a single alternate frame.
    expect(() => rerender(<FrameStepper frames={[multi[0]]} />)).not.toThrow();
    expect(container.querySelector(".frame-stepper-count")).toBeNull();
    expect(container.textContent).not.toMatch(/Something broke/);
    const svgs = queryAllDeep(container, "svg");
    expect(svgs.length).toBeGreaterThan(0);
    cleanup();
  });

  it("drops malformed frames so holes never reach TeachRenderBox", () => {
    const { container, cleanup } = render(
      <FrameStepper
        frames={[undefined as unknown as (typeof frames)[0], frames[0], null as unknown as (typeof frames)[0]]}
      />,
    );
    expect(container.querySelector(".frame-stepper")).not.toBeNull();
    expect(queryAllDeep(container, "svg").length).toBe(1);
    cleanup();
  });
});
