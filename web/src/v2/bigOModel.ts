/**
 * Verified, deterministic Big O toy-work model used by words, graph and game.
 * Counts represent stick placements, not measured runtime or an arbitrary
 * algorithm's exact instruction count. Refs #185 and #204.
 */
import { targetSticks, type ComplexityMode } from "../visuals/SticksBoxesComplexity";

export const BIG_O_TERMS = [
  {
    symbol: "n",
    definition: "The number of boxes (input items) in this small example. Increasing n makes the example bigger.",
  },
  {
    symbol: "O(…)",
    definition: "A growth class: how work scales for larger inputs. It does not promise an exact number of real CPU operations.",
  },
] as const;

export const BIG_O_RULES: Record<ComplexityMode, { title: string; action: string; pattern: string }> = {
  "O(1)": {
    title: "Constant",
    action: "Place one stick in the first box, regardless of how many boxes there are.",
    pattern: "One placement no matter how large n becomes.",
  },
  "O(n)": {
    title: "Linear",
    action: "Put one stick in each box, so the number of placements matches n.",
    pattern: "Twice as many boxes means twice as many placements.",
  },
  "O(n²)": {
    title: "Quadratic",
    action: "Pair every box with every box, including itself. Each pair costs one stick.",
    pattern: "Twice as many boxes means four times as many placements.",
  },
};

export function exampleWork(mode: ComplexityMode, n: number): number {
  if (!Number.isInteger(n) || n < 1 || n > 8) {
    throw new RangeError("Big O toy example size n must be an integer from 1 to 8");
  }
  return targetSticks(mode, n);
}

export function exactEquation(mode: ComplexityMode, n: number): string {
  const count = exampleWork(mode, n);
  if (mode === "O(1)") return `${n} boxes → 1 stick`;
  if (mode === "O(n)") return `${n} boxes → ${count} sticks`;
  return `${n} × ${n} pairs = ${count} sticks`;
}

export function curvePoints(mode: ComplexityMode): { n: number; work: number }[] {
  return Array.from({ length: 8 }, (_, i) => {
    const n = i + 1;
    return { n, work: exampleWork(mode, n) };
  });
}

export function challengeSize(n: number): number {
  if (!Number.isInteger(n) || n < 2 || n > 8) throw new RangeError("Invalid challenge size");
  return n === 8 ? 7 : n + 1;
}
