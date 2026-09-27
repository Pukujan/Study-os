import { describe, expect, it } from "vitest";
import type { WorkedExample } from "../api";
import { workedExampleParts } from "./workedExample";

const loose = (value: unknown) => value as WorkedExample;

describe("workedExampleParts", () => {
  it("reads a single md block", () => {
    expect(workedExampleParts({ md: "Solve it." })).toEqual({ md: "Solve it.", steps: [], frames: [] });
  });

  it("reads steps_md", () => {
    const parts = workedExampleParts({ steps_md: ["first", "second"] });
    expect(parts.md).toBeNull();
    expect(parts.steps).toEqual(["first", "second"]);
  });

  it("survives the stripped payload that caused the blank play screen (#126)", () => {
    expect(workedExampleParts(loose({ frames: [] }))).toEqual({ md: null, steps: [], frames: [] });
    expect(workedExampleParts(loose({}))).toEqual({ md: null, steps: [], frames: [] });
    expect(workedExampleParts(undefined)).toEqual({ md: null, steps: [], frames: [] });
  });

  it("keeps renderable frames and drops malformed ones", () => {
    const parts = workedExampleParts(
      loose({ frames: [{ type: "box_index", array: [1], show_positions: true, show_indices: false }, null, "junk"] }),
    );
    expect(parts.frames).toHaveLength(1);
  });
});