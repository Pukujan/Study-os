import { describe, expect, it } from "vitest";
import { isRenderableFrame, sanitizeFrames } from "./frames";

describe("sanitizeFrames / isRenderableFrame", () => {
  it("accepts frames with a string type", () => {
    expect(isRenderableFrame({ type: "growth_curve", n_values: [2] })).toBe(true);
  });

  it("rejects null, undefined, and untyped objects", () => {
    expect(isRenderableFrame(null)).toBe(false);
    expect(isRenderableFrame(undefined)).toBe(false);
    expect(isRenderableFrame({})).toBe(false);
    expect(isRenderableFrame({ type: 1 })).toBe(false);
  });

  it("drops holes so Explain-again rotate cannot ship undefined slots", () => {
    const cleaned = sanitizeFrames([
      { type: "growth_workers", n_values: [2] },
      null,
      undefined,
      { type: "growth_curve", n_values: [4] },
      { nope: true },
    ]);
    expect(cleaned).toHaveLength(2);
    expect(cleaned.every((f) => typeof f.type === "string")).toBe(true);
  });

  it("returns [] for non-arrays", () => {
    expect(sanitizeFrames(null)).toEqual([]);
    expect(sanitizeFrames(undefined)).toEqual([]);
    expect(sanitizeFrames("x")).toEqual([]);
  });
});
