// Frozen judge prompt and closed verdict code set for the SOS-0017 gate.
//
// The prompt is deliberately short and code-constrained: a free-text blessing
// cannot be parsed into a gate verdict, and a long rubric invites
// informativeness bias (a judge scoring the prompt text instead of the image).

export const VISION_CODES = [
  "VISION_PASS",
  "VISION_FAIL_BLANK",
  "VISION_FAIL_PARTIAL",
  "VISION_FAIL_WRONG_TARGET",
  "VISION_FAIL_UNREADABLE",
  "VISION_UNCERTAIN",
  "VISION_MALFORMED",
  "VISION_PROVIDER_ERROR",
  "VISION_NOT_RUN",
  "VISION_HOLDOUT_BROKEN",
] as const;

export type VisionCode = (typeof VISION_CODES)[number];

/** Codes the judge may return for one image; the rest are gate-side states. */
export const JUDGE_CODES = [
  "VISION_PASS",
  "VISION_FAIL_BLANK",
  "VISION_FAIL_PARTIAL",
  "VISION_FAIL_WRONG_TARGET",
  "VISION_FAIL_UNREADABLE",
  "VISION_UNCERTAIN",
] as const satisfies readonly VisionCode[];

export const PASS_CODE: VisionCode = "VISION_PASS";
export const MALFORMED_CODE: VisionCode = "VISION_MALFORMED";
export const PROVIDER_ERROR_CODE: VisionCode = "VISION_PROVIDER_ERROR";
export const NOT_RUN_CODE: VisionCode = "VISION_NOT_RUN";
export const HOLDOUT_BROKEN_CODE: VisionCode = "VISION_HOLDOUT_BROKEN";

export const TARGET_DESCRIPTION =
  "the learner step-review surface of a study app: a panel with five numbered rating controls (1 to 5), a text field labelled 'Why this rating?', and a Submit button";

export const VISION_PROMPT = [
  "You are checking one screenshot of a web app. Judge only what is visible in this image.",
  "Do not assume the interface is correct because of how this instruction is worded.",
  `The target is ${TARGET_DESCRIPTION}.`,
  "Answer with exactly two lines:",
  "line 1: one code from this closed set, nothing else:",
  "VISION_PASS - the step-review surface is visibly rendered: five rating controls, a why text field and a Submit control are identifiable",
  "VISION_FAIL_BLANK - the canvas is empty, all-white or near-uniform, or shows no interface at all",
  "VISION_FAIL_PARTIAL - some but not all of the required controls are identifiable",
  "VISION_FAIL_WRONG_TARGET - an interface is rendered, but it is not the step-review surface",
  "VISION_FAIL_UNREADABLE - rendering is present but clipped, overlapping, cut off or otherwise unreadable",
  "VISION_UNCERTAIN - you cannot decide from this image; this is treated as a failure, never a pass",
  "line 2: a short locator for what you looked at, or the reason you failed.",
].join("\n");

/** First line of a judge reply, normalised for comparison against the closed set. */
export function parseVerdictCode(reply: string): VisionCode {
  const firstLine = (reply ?? "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find((line) => line.length > 0);
  // The verdict must be the first token of the first line; anything else is
  // malformed rather than "close enough" (a code is never inferred from prose).
  const token = ((firstLine ?? "").split(/\s+/)[0] ?? "").replace(/[^A-Za-z_]/g, "").toUpperCase();
  return (JUDGE_CODES as readonly string[]).includes(token) ? (token as VisionCode) : MALFORMED_CODE;
}

/** Second line of a judge reply: the locator, truncated for the receipt. */
export function parseLocator(reply: string): string {
  const lines = (reply ?? "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  return (lines[1] ?? "").slice(0, 300);
}
