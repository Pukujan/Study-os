/**
 * InferHub vision prompts that verify a live TeachRenderBox screenshot
 * against a curated research reference — match only, never generate.
 * Refs #161 #126
 */

export type CuratedMatchSpec = {
  asset_id: string;
  reference_src: string;
  expect: string;
};

export const BIG_O_MULTI_CLASS: CuratedMatchSpec = {
  asset_id: "big-o.comparison-computational-complexity",
  reference_src: "/teach-visuals/big-o/comparison-computational-complexity.svg",
  expect:
    "a growth chart with multiple complexity families (at least O(1), O(log n), O(n), O(n²) or equivalent curves) on shared axes — not a stick-figure worker metaphor and not only two unlabeled slow/fast lines",
};

export const FRACTION_NUMBER_LINE: CuratedMatchSpec = {
  asset_id: "fractions.propia-en-recta",
  reference_src: "/teach-visuals/fractions/fraccion-propia-en-la-recta.png",
  expect:
    "a fraction teach surface that includes a number line with fraction marks (magnitude), not area bars alone",
};

export function curatedMatchPrompt(spec: CuratedMatchSpec): string {
  return [
    "You are checking one screenshot of a study lesson visual.",
    "Judge only what is visible. Do not invent missing UI.",
    `Curated reference asset_id=${spec.asset_id} src=${spec.reference_src}.`,
    `The live teach island should match this research visual type: ${spec.expect}.`,
    "Answer with exactly two lines:",
    "line 1: one code from: VISION_PASS | VISION_FAIL_PARTIAL | VISION_FAIL_WRONG_TARGET | VISION_FAIL_UNREADABLE | VISION_UNCERTAIN",
    "VISION_PASS - the screenshot visually matches the curated multi-class / number-line expectation",
    "VISION_FAIL_WRONG_TARGET - invent-first metaphor (e.g. stick workers only) or slow-vs-fast-only Big O, or missing number line for fractions",
    "line 2: short locator for what you saw.",
  ].join("\n");
}
