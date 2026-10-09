/**
 * Computer-authored finite missions. No learner-controlled Big O selector;
 * classification is disclosed *after* the concrete actions are completed.
 * This is a deterministic teaching sandbox, not a mastery diagnosis.
 */
import { exampleWork } from "./bigOModel";
import type { ComplexityMode } from "../visuals/SticksBoxesComplexity";

export type GrowthMission = {
  id: string;
  n: number;
  mode: ComplexityMode;
  heading: string;
  instruction: string;
  actionHint: string;
};

export const GROWTH_MISSIONS: readonly GrowthMission[] = [
  {
    id: "cover-three", n: 3, mode: "O(n)",
    heading: "One stick for every box",
    instruction: "You have three boxes. Your job is to put exactly one stick into each box.",
    actionHint: "Every box needs one stick. You can choose which box to fill first.",
  },
  {
    id: "cover-four", n: 4, mode: "O(n)",
    heading: "What happens with one more box?",
    instruction: "The computer added one box. Repeat the same rule: one stick per box.",
    actionHint: "Notice how the live work counter changes compared with the last round.",
  },
  {
    id: "pairs-three", n: 3, mode: "O(n²)",
    heading: "Every box meets every box",
    instruction: "Make each ordered pair once. A box can pair with itself. Drag a stick to each pair tile.",
    actionHint: "A pair like 1→2 and 2→1 counts as two different directions.",
  },
  {
    id: "pairs-four", n: 4, mode: "O(n²)",
    heading: "One extra box, many extra pairs",
    instruction: "There are four boxes now. Fill every ordered pair, including self-pairs.",
    actionHint: "Compare the growth of the pair board with the one-stick-per-box rounds.",
  },
  {
    id: "first-only", n: 4, mode: "O(1)",
    heading: "Only the first box matters",
    instruction: "The computer only needs a stick in Box 1, no matter how many other boxes exist.",
    actionHint: "Try choosing another box first. The board will explain why it is not allowed.",
  },
] as const;

export function requiredTargets(mission: GrowthMission): string[] {
  if (!Number.isInteger(mission.n) || mission.n < 1 || mission.n > 8) throw new RangeError("Invalid mission input size");
  if (mission.mode === "O(1)") return ["box:0"];
  if (mission.mode === "O(n)") return Array.from({ length: mission.n }, (_, i) => `box:${i}`);
  return Array.from({ length: mission.n * mission.n }, (_, k) =>
    `pair:${Math.floor(k / mission.n)}:${k % mission.n}`);
}

export type PlacementVerdict = "accepted" | "duplicate" | "not-allowed";
export function validatePlacement(mission: GrowthMission, filled: readonly string[], target: string): PlacementVerdict {
  if (!requiredTargets(mission).includes(target)) return "not-allowed";
  if (filled.includes(target)) return "duplicate";
  return "accepted";
}

export function missionComplete(mission: GrowthMission, filled: readonly string[]): boolean {
  const expected = requiredTargets(mission);
  return filled.length === expected.length && new Set(filled).size === filled.length &&
    filled.every((id) => expected.includes(id)) && expected.length === exampleWork(mission.mode, mission.n);
}
