import { describe, expect, it } from "vitest";
import { targetSticks, type ComplexityMode } from "../visuals/SticksBoxesComplexity";
import { BIG_O_TERMS, challengeSize, curvePoints, exactEquation, exampleWork } from "./bigOModel";

const modes: ComplexityMode[] = ["O(1)", "O(n)", "O(n²)"];

describe("v2 Big O shared semantic model (Refs #204)", () => {
  it("defines the input, illustrative work and asymptotic notation before use", () => {
    expect(BIG_O_TERMS.map((term) => term.symbol)).toEqual(["n", "O(…)"]);
    expect(BIG_O_TERMS.every((term) => term.definition.length > 20)).toBe(true);
  });

  it("makes graph, algebra and original learner game agree on every n", () => {
    for (const mode of modes) {
      const points = curvePoints(mode);
      expect(points).toHaveLength(8);
      for (let n = 2; n <= 8; n++) {
        const work = targetSticks(mode, n);
        expect(exampleWork(mode, n)).toBe(work);
        expect(points.find((p) => p.n === n)?.work).toBe(work);
        expect(exactEquation(mode, n)).toContain(String(work));
      }
    }
  });

  it("fails closed on invalid sizes rather than rendering impossible work", () => {
    expect(() => exampleWork("O(n²)", 0)).toThrow(RangeError);
    expect(() => exampleWork("O(n)", 3.5)).toThrow(RangeError);
    expect(() => exampleWork("O(n)", 9)).toThrow(RangeError);
  });

  it("uses a different input for the transfer question", () => {
    for (let n = 2; n <= 8; n++) {
      expect(challengeSize(n)).not.toBe(n);
      expect(challengeSize(n)).toBeGreaterThanOrEqual(2);
      expect(challengeSize(n)).toBeLessThanOrEqual(8);
    }
  });
});
