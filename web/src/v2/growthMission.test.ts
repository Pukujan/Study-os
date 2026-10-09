import { describe, expect, it } from "vitest";
import { GROWTH_MISSIONS, missionComplete, requiredTargets, validatePlacement } from "./growthMission";
import { exampleWork } from "./bigOModel";

describe("computer-led growth missions (#204)", () => {
  it("assigns rules without a learner-selectable difficulty or Big O mode", () => {
    expect(GROWTH_MISSIONS.map((mission) => mission.mode)).toEqual(["O(n)", "O(n)", "O(n²)", "O(n²)", "O(1)"]);
    expect(GROWTH_MISSIONS.every((mission) => !!mission.instruction && mission.n >= 3)).toBe(true);
  });
  it("requires every valid unique placement and rejects duplicate/invalid moves", () => {
    for (const mission of GROWTH_MISSIONS) {
      const target = requiredTargets(mission);
      expect(target.length).toBe(exampleWork(mission.mode, mission.n));
      expect(missionComplete(mission, target.slice(0, -1))).toBe(false);
      expect(missionComplete(mission, target)).toBe(true);
      expect(missionComplete(mission, [...target, target[0]])).toBe(false);
      expect(validatePlacement(mission, [], target[0])).toBe("accepted");
      expect(validatePlacement(mission, [target[0]], target[0])).toBe("duplicate");
      expect(validatePlacement(mission, [], "pair:99:99")).toBe("not-allowed");
    }
  });
  it("treats different pair directions as separate actions", () => {
    const pair = GROWTH_MISSIONS.find((m) => m.mode === "O(n²)")!;
    expect(requiredTargets(pair)).toContain("pair:0:1");
    expect(requiredTargets(pair)).toContain("pair:1:0");
  });
  it("first-only task refuses other boxes", () => {
    const first = GROWTH_MISSIONS.at(-1)!;
    expect(validatePlacement(first, [], "box:1")).toBe("not-allowed");
    expect(validatePlacement(first, [], "box:0")).toBe("accepted");
  });
});
