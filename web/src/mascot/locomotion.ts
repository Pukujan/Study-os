/**
 * Mascot locomotion FSM (SOS-0014).
 *
 * Pure reducer: same state + same event + same rand sequence => same state.
 * No timers, no wall clock, no DOM — the component owns the clock and feeds
 * `tick`, so the whole thing is testable with a seeded sweep.
 *
 * Three deliberate design rules:
 *
 * 1. Facing flips ONLY on `turnDone`. A direction request therefore routes
 *    through the `turn` one-shot instead of snapping, so the pet never reverses
 *    mid-stride (M-P3).
 * 2. The walk cycle is advanced by DISTANCE travelled, not elapsed time. That
 *    is how a walk cycle should read on screen (feet stay planted while the
 *    body glides) and it keeps `frame` monotonic instead of free-running on a
 *    wall clock.
 * 3. Timed one-shots (turn, oneShot) complete from `tick` alone, using their
 *    own sheet duration. The caller may still send `turnDone`/`oneShotEnd`
 *    early to cut a phase short; both are idempotent when the phase is over.
 *
 * Idle leaves `frame` alone — Sprite owns the idle loop via CSS.
 */

export type Facing = "left" | "right";
export type PoseActivity = "idle" | "walk" | "turn" | "oneShot";
export type OneShotMood = "wave" | "celebrate" | "encourage" | "headpat" | "starplay";

export type PoseEvent =
  | { type: "startWalk"; x: number; y: number }
  | { type: "tick"; dtMs: number }
  | { type: "arrive" }
  | { type: "turnDone" }
  | { type: "oneShotEnd" }
  | { type: "idle" }
  | { type: "queueOneShot"; mood: OneShotMood }
  | { type: "setFacing"; facing: Facing }
  | { type: "reverse" };

export type PoseState = {
  activity: PoseActivity;
  facing: Facing;
  frame: number;
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  mood: OneShotMood | null;
  queuedMood: OneShotMood | null;
  resumeAfterTurn: boolean;
  frameAccMs: number;
  strideAccPx: number;
  phaseMs: number;
  speedPxPerMs: number;
};

/**
 * Frame counts and rates mirror web/public/mascot/manifest.json (walk/turn) and
 * Pet's existing idle/one-shot cadence. Keep in step with the manifest.
 */
export const LOCOMOTION_SHEETS: Record<PoseActivity, { frames: number; fps: number }> = {
  walk: { frames: 6, fps: 8 },
  turn: { frames: 4, fps: 8 },
  oneShot: { frames: 6, fps: 5 },
  idle: { frames: 6, fps: 4 },
};

const BASE_WALK_SPEED_PX_PER_MS = 0.32;
const STRIDE_PX = 120;

function phaseDurationMs(activity: PoseActivity): number {
  const { frames, fps } = LOCOMOTION_SHEETS[activity];
  return (frames / fps) * 1000;
}

export function initialPoseState(facing: Facing): PoseState {
  return {
    activity: "idle",
    facing,
    frame: 0,
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    mood: null,
    queuedMood: null,
    resumeAfterTurn: false,
    frameAccMs: 0,
    strideAccPx: 0,
    phaseMs: 0,
    speedPxPerMs: BASE_WALK_SPEED_PX_PER_MS,
  };
}

/**
 * Wrap (never zero) the frame on an activity change. Zeroing would make the
 * rendered frame jump backwards whenever the pet arrives, and walk, idle and
 * oneShot are all 6-frame sheets, so wrapping is a no-op for those transitions.
 */
function withActivity(state: PoseState, activity: PoseActivity): PoseState {
  const frames = LOCOMOTION_SHEETS[activity].frames;
  return {
    ...state,
    activity,
    frame: state.frame % frames,
    frameAccMs: 0,
    strideAccPx: 0,
    phaseMs: 0,
  };
}

function advanceTimedFrame(state: PoseState, dtMs: number): PoseState {
  const { frames, fps } = LOCOMOTION_SHEETS[state.activity];
  const frameMs = 1000 / fps;
  let acc = state.frameAccMs + dtMs;
  let frame = state.frame;
  while (acc >= frameMs) {
    acc -= frameMs;
    frame = (frame + 1) % frames;
  }
  return { ...state, frame, frameAccMs: acc };
}

/**
 * At most one frame per tick: a backgrounded tab that resumes with a huge
 * `dtMs` must not fast-forward the whole cycle in one go.
 */
function advanceWalkFrame(state: PoseState, travelledPx: number): PoseState {
  const acc = state.strideAccPx + travelledPx;
  if (acc < STRIDE_PX) return { ...state, strideAccPx: acc };
  return { ...state, frame: (state.frame + 1) % LOCOMOTION_SHEETS.walk.frames, strideAccPx: 0 };
}

function arriveAt(state: PoseState): PoseState {
  if (state.queuedMood) {
    const next = withActivity(state, "oneShot");
    return { ...next, mood: state.queuedMood, queuedMood: null };
  }
  return withActivity(state, "idle");
}

function enterTurn(state: PoseState, resumeAfterTurn: boolean, mirrorTarget: boolean): PoseState {
  const next = withActivity(state, "turn");
  return {
    ...next,
    resumeAfterTurn,
    targetX: mirrorTarget ? state.x * 2 - state.targetX : state.targetX,
    targetY: mirrorTarget ? state.y * 2 - state.targetY : state.targetY,
  };
}

export function reducePose(state: PoseState, event: PoseEvent, rand: () => number): PoseState {
  switch (event.type) {
    case "startWalk": {
      const dist = Math.hypot(event.x - state.x, event.y - state.y);
      const next = withActivity(state, "walk");
      // A zero-length walk would otherwise never satisfy the arrival test.
      if (dist === 0) {
        return arriveAt({ ...next, x: event.x, y: event.y, targetX: event.x, targetY: event.y });
      }
      return {
        ...next,
        targetX: event.x,
        targetY: event.y,
        speedPxPerMs: BASE_WALK_SPEED_PX_PER_MS * (0.9 + rand() * 0.2),
      };
    }

    case "tick": {
      if (state.activity === "walk") {
        const dx = state.targetX - state.x;
        const dy = state.targetY - state.y;
        const remaining = Math.hypot(dx, dy);
        const step = state.speedPxPerMs * event.dtMs;
        if (remaining <= step) {
          return arriveAt(
            advanceWalkFrame({ ...state, x: state.targetX, y: state.targetY }, remaining),
          );
        }
        return advanceWalkFrame(
          { ...state, x: state.x + (dx / remaining) * step, y: state.y + (dy / remaining) * step },
          step,
        );
      }

      if (state.activity === "turn") {
        const advanced = advanceTimedFrame(state, event.dtMs);
        const phaseMs = advanced.phaseMs + event.dtMs;
        if (phaseMs >= phaseDurationMs("turn")) {
          return reducePose({ ...advanced, phaseMs }, { type: "turnDone" }, rand);
        }
        return { ...advanced, phaseMs };
      }

      if (state.activity === "oneShot") {
        const advanced = advanceTimedFrame(state, event.dtMs);
        const phaseMs = advanced.phaseMs + event.dtMs;
        if (phaseMs >= phaseDurationMs("oneShot")) {
          return reducePose({ ...advanced, phaseMs }, { type: "oneShotEnd" }, rand);
        }
        return { ...advanced, phaseMs };
      }

      return state;
    }

    case "arrive":
      return state.activity === "walk" ? arriveAt(state) : state;

    case "turnDone": {
      if (state.activity !== "turn") return state;
      const facing: Facing = state.facing === "left" ? "right" : "left";
      const turned = { ...state, facing, resumeAfterTurn: false };
      return state.resumeAfterTurn ? withActivity(turned, "walk") : withActivity(turned, "idle");
    }

    case "oneShotEnd":
      return state.activity === "oneShot" ? withActivity({ ...state, mood: null }, "idle") : state;

    case "idle":
      // Walking owns the pose until it arrives (M-P2: no simultaneous walk+idle).
      if (state.activity === "walk") return state;
      return withActivity({ ...state, mood: null, queuedMood: null, resumeAfterTurn: false }, "idle");

    case "queueOneShot": {
      if (state.activity === "walk" || state.activity === "turn") {
        return { ...state, queuedMood: event.mood };
      }
      return { ...withActivity(state, "oneShot"), mood: event.mood, queuedMood: null };
    }

    case "setFacing": {
      if (event.facing === state.facing) return state;
      return enterTurn(state, state.activity === "walk", false);
    }

    case "reverse": {
      if (state.activity === "turn") return state;
      const wasWalking = state.activity === "walk";
      return enterTurn(state, wasWalking, wasWalking);
    }
  }
}
