import { describe, expect, it } from "vitest";
import { shouldVisit, type VisitContext } from "./visitRules";

const base: VisitContext = {
  idleSeconds: 120,
  lastVisitSeconds: null,
  probeOpen: false,
  typing: false,
  speaking: false,
  petTalking: false,
  petThinking: false,
  reducedMotion: false,
  petHidden: false,
};

describe("shouldVisit", () => {
  it("allows a rare idle visit", () => {
    expect(shouldVisit(base)).toBe(true);
  });
  it("blocks during assessment probe, typing, speaking, pet activity, reduced motion, hidden, or too soon", () => {
    expect(shouldVisit({ ...base, probeOpen: true })).toBe(false);
    expect(shouldVisit({ ...base, typing: true })).toBe(false);
    expect(shouldVisit({ ...base, speaking: true })).toBe(false);
    expect(shouldVisit({ ...base, petTalking: true })).toBe(false);
    expect(shouldVisit({ ...base, petThinking: true })).toBe(false);
    expect(shouldVisit({ ...base, reducedMotion: true })).toBe(false);
    expect(shouldVisit({ ...base, petHidden: true })).toBe(false);
    expect(shouldVisit({ ...base, idleSeconds: 30 })).toBe(false);
    expect(shouldVisit({ ...base, lastVisitSeconds: 120 })).toBe(false);
  });
});
