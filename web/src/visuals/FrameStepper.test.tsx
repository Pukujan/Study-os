import { describe, expect, it } from "vitest";
import { act } from "react";
import FrameStepper from "./FrameStepper";
import { render } from "../test-utils";

const frames = [
  { type: "fraction_bar" as const, bars: [{ parts: 2, shaded: 1 }] },
  { type: "fraction_bar" as const, bars: [{ parts: 3, shaded: 2 }] },
  { type: "fraction_bar" as const, bars: [{ parts: 4, shaded: 3 }] },
];

describe("FrameStepper", () => {
  it("shows one frame at a time and no controls for a single frame", () => {
    const { container, cleanup } = render(<FrameStepper frames={[{ type: "fraction_bar" as const, bars: [{ parts: 2, shaded: 1 }] }]} />);
    const svgs = container.querySelectorAll("svg");
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
});
