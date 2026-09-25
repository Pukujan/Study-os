import { describe, expect, it } from "vitest";
import {
  reducePose,
  initialPoseState,
  type PoseEvent,
  type PoseState,
} from "./locomotion";

/**
 * M-P1 frame index bounds: every state reachable through reducePose keeps
 * frame in [0, frames) for the active sheet.
 * M-P2 discriminated union: walk + idle cannot coexist (single activity tag).
 * M-P3 facing changes only via turn/reverse events.
 */

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const EVENTS: PoseEvent[] = [
  { type: "startWalk", x: 120, y: 300 },
  { type: "tick", dtMs: 50 },
  { type: "arrive" },
  { type: "turnDone" },
  { type: "oneShotEnd" },
  { type: "idle" },
  { type: "queueOneShot", mood: "wave" },
  { type: "setFacing", facing: "left" },
  { type: "reverse" },
];

function frameCountFor(state: PoseState): number {
  // Locomotion sheets under test: walk = 6-frame loop, turn = 4-frame one-shot,
  // idle = 6-frame loop (manifest values; see web/public/mascot/manifest.json).
  switch (state.activity) {
    case "walk":
      return 6;
    case "turn":
      return 4;
    case "oneShot":
      return 6;
    default:
      return 6;
  }
}

describe("M-P1 frame index bounds (seeded sweep 100 x 200 events)", () => {
  it("never renders an out-of-range frame", () => {
    for (let seed = 0; seed < 100; seed++) {
      const rand = mulberry32(seed);
      let state: PoseState = initialPoseState("right");
      for (let i = 0; i < 200; i++) {
        const event = EVENTS[Math.floor(rand() * EVENTS.length)];
        state = reducePose(state, event, rand);
        const frames = frameCountFor(state);
        expect(
          Number.isInteger(state.frame) && state.frame >= 0 && state.frame < frames,
          `seed=${seed} step=${i} event=${event.type} state=${JSON.stringify(state)}`,
        ).toBe(true);
        // M-P2: discriminated union — exactly one activity tag exists.
        const tags = ["idle", "walk", "turn", "oneShot"] as const;
        const active = tags.filter((t) => state.activity === t);
        expect(active.length).toBe(1);
      }
    }
  });

  it("walk frame advances monotonically per tick without skipping the sheet", () => {
    let state: PoseState = reducePose(initialPoseState("right"), { type: "startWalk", x: 500, y: 300 }, mulberry32(1));
    for (let i = 0; i < 30; i++) {
      const prev = state.frame;
      state = reducePose(state, { type: "tick", dtMs: 125 }, mulberry32(2));
      expect(state.frame).toBeGreaterThanOrEqual(0);
      expect(state.frame).toBeLessThan(6);
      expect(Math.abs(state.frame - prev)).toBeLessThanOrEqual(1);
    }
  });
});

describe("M-P2 no simultaneous walk + idle", () => {
  it("startWalk from idle yields walk (not idle) on the next state", () => {
    const state = reducePose(initialPoseState("right"), { type: "startWalk", x: 10, y: 10 }, mulberry32(3));
    expect(state.activity).toBe("walk");
    expect(state.activity).not.toBe("idle");
  });

  it("ignores idle transition while walking", () => {
    let state = reducePose(initialPoseState("right"), { type: "startWalk", x: 500, y: 300 }, mulberry32(4));
    state = reducePose(state, { type: "idle" }, mulberry32(5));
    expect(state.activity).toBe("walk");
  });

  it("one-shot interactions queue after arrival, not during walk", () => {
    let state = reducePose(initialPoseState("right"), { type: "startWalk", x: 900, y: 300 }, mulberry32(6));
    state = reducePose(state, { type: "queueOneShot", mood: "wave" }, mulberry32(7));
    // queued, not playing yet
    expect(state.activity).toBe("walk");
    // walk until arrival
    for (let i = 0; i < 60 && state.activity === "walk"; i++) {
      state = reducePose(state, { type: "tick", dtMs: 100 }, mulberry32(8));
    }
    expect(state.activity).not.toBe("walk");
  });
});

describe("M-P3 facing changes only via turn/reverse", () => {
  it("a bare setFacing while walking routes through turn, not an instant flip", () => {
    let state = reducePose(initialPoseState("right"), { type: "startWalk", x: 900, y: 300 }, mulberry32(9));
    state = reducePose(state, { type: "setFacing", facing: "left" }, mulberry32(10));
    expect(state.facing).toBe("right"); // unchanged until turn completes
    expect(["turn", "walk"]).toContain(state.activity);
  });

  it("seeded sweep: facing deltas co-occur only with turn/reverse completion", () => {
    for (let seed = 0; seed < 100; seed++) {
      const rand = mulberry32(1000 + seed);
      let state: PoseState = initialPoseState("right");
      let lastEvent = "init";
      for (let i = 0; i < 200; i++) {
        const event = EVENTS[Math.floor(rand() * EVENTS.length)];
        const before = state.facing;
        state = reducePose(state, event, rand);
        if (state.facing !== before) {
          expect(
            ["turnDone", "reverse"].includes(lastEvent) || event.type === "reverse" || event.type === "turnDone",
            `seed=${seed} step=${i}: facing changed ${before}->${state.facing} after event=${event.type}`,
          ).toBe(true);
        }
        lastEvent = event.type;
      }
    }
  });

  it("reverse during walk enters turn one-shot then exits with facing flipped", () => {
    let state = reducePose(initialPoseState("right"), { type: "startWalk", x: 900, y: 300 }, mulberry32(11));
    state = reducePose(state, { type: "reverse" }, mulberry32(12));
    expect(state.activity).toBe("turn");
    const before = state.facing;
    state = reducePose(state, { type: "turnDone" }, mulberry32(13));
    expect(state.facing).not.toBe(before);
    expect(state.activity).not.toBe("turn");
  });
});
