import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Sprite from "./Sprite";
import {
  LOCOMOTION_SHEETS,
  initialPoseState,
  reducePose,
  type PoseState,
} from "./locomotion";

export type PetMood = "idle" | "wave" | "thinking" | "talking" | "celebrate" | "encourage";

const MOODS: Record<PetMood, { src: string; frames: number; frameW: number; frameH: number }> = {
  idle: { src: "/mascot/pet-idle.webp", frames: 6, frameW: 144, frameH: 176 },
  wave: { src: "/mascot/pet-wave.webp", frames: 6, frameW: 144, frameH: 176 },
  thinking: { src: "/mascot/pet-thinking.webp", frames: 6, frameW: 144, frameH: 176 },
  talking: { src: "/mascot/pet-talking.webp", frames: 6, frameW: 144, frameH: 176 },
  celebrate: { src: "/mascot/pet-celebrate.webp", frames: 6, frameW: 144, frameH: 176 },
  encourage: { src: "/mascot/pet-encourage.webp", frames: 6, frameW: 144, frameH: 176 },
};

// SOS-0014 locomotion sheets. Both are multi-row grids, so they are always
// driven with an explicit `frame` from the FSM rather than the CSS animation.
const WALK = { src: "/mascot/pet-walk.webp", frames: 6, frameW: 144, frameH: 176, cols: 3 };
const TURN = { src: "/mascot/pet-turn.webp", frames: 4, frameW: 144, frameH: 176, cols: 2 };
const TURN_MS = (LOCOMOTION_SHEETS.turn.frames / LOCOMOTION_SHEETS.turn.fps) * 1000;
const ONE_SHOT_MS = (LOCOMOTION_SHEETS.oneShot.frames / LOCOMOTION_SHEETS.oneShot.fps) * 1000;

const HIDDEN_KEY = "sos.pet.hidden";
const POS_KEY = "sos.pet.pos";
const TIP_KEY = "sos.pet.tipSeen";

type Pos = { x: number; y: number };

export function usePetHidden(initial?: boolean) {
  const [hidden, setHidden] = useState(() => {
    if (typeof window === "undefined") return initial ?? false;
    const stored = localStorage.getItem(HIDDEN_KEY);
    return stored ? stored === "true" : (initial ?? false);
  });
  const setPersisted = (v: boolean) => {
    setHidden(v);
    if (typeof window !== "undefined") localStorage.setItem(HIDDEN_KEY, String(v));
  };
  return [hidden, setPersisted] as const;
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia(query);
    setMatches(mq.matches);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    if (mq.addEventListener) {
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
    const legacy = mq as unknown as {
      addListener: (h: (e: MediaQueryListEvent) => void) => void;
      removeListener: (h: (e: MediaQueryListEvent) => void) => void;
    };
    const wrapped = (e: MediaQueryListEvent) => handler(e);
    legacy.addListener(wrapped);
    return () => legacy.removeListener(wrapped);
  }, [query]);
  return matches;
}

function readSessionPos(): Pos | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(POS_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw) as Pos;
    if (typeof p.x === "number" && typeof p.y === "number") return p;
  } catch {
    /* ignore */
  }
  return null;
}

function writeSessionPos(p: Pos): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(POS_KEY, JSON.stringify(p));
}

function tipAlreadySeen(): boolean {
  if (typeof window === "undefined") return true;
  return sessionStorage.getItem(TIP_KEY) === "1";
}

function markTipSeen(): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(TIP_KEY, "1");
}

function collectAvoidRects(): DOMRect[] {
  if (typeof document === "undefined") return [];
  const sels = [
    ".probe .markdown",
    ".probe .free",
    ".probe .choices",
    ".probe-actions",
    ".feedback .btn.primary",
    ".teach .markdown",
    ".progress",
    "header, .topbar, .shell-header",
  ];
  const out: DOMRect[] = [];
  for (const sel of sels) {
    document.querySelectorAll(sel).forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) out.push(r);
    });
  }
  return out;
}

function overlapArea(a: { x: number; y: number; w: number; h: number }, b: DOMRect): number {
  const x1 = Math.max(a.x, b.left);
  const y1 = Math.max(a.y, b.top);
  const x2 = Math.min(a.x + a.w, b.right);
  const y2 = Math.min(a.y + a.h, b.bottom);
  return Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
}

function scorePos(x: number, y: number, w: number, h: number, avoid: DOMRect[]): number {
  let score = 0;
  const box = { x, y, w, h };
  for (const r of avoid) score += overlapArea(box, r);
  const cx = x + w / 2;
  const cy = y + h / 2;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  score += Math.abs(cx - vw * 0.78) * 0.05 + Math.abs(cy - vh * 0.72) * 0.05;
  return score;
}

function clampPos(x: number, y: number, w: number, h: number, pad: number): Pos {
  const maxX = Math.max(pad, window.innerWidth - w - pad);
  const maxY = Math.max(pad, window.innerHeight - h - pad);
  return {
    x: Math.min(maxX, Math.max(pad, x)),
    y: Math.min(maxY, Math.max(pad, y)),
  };
}

function defaultPos(w: number, h: number): Pos {
  const pad = 16;
  return clampPos(window.innerWidth - w - pad - 8, window.innerHeight - h - 96, w, h, pad);
}

function pickWanderTarget(w: number, h: number): Pos {
  const pad = 16;
  const avoid = collectAvoidRects();
  let best = defaultPos(w, h);
  let bestScore = Number.POSITIVE_INFINITY;
  for (let i = 0; i < 14; i++) {
    const x = pad + Math.random() * Math.max(1, window.innerWidth - w - pad * 2);
    const y = pad + Math.random() * Math.max(1, window.innerHeight - h - pad * 2 - 48);
    const p = clampPos(x, y, w, h, pad);
    const s = scorePos(p.x, p.y, w, h, avoid);
    if (s < bestScore) {
      bestScore = s;
      best = p;
    }
  }
  return best;
}

export default function Pet({
  mood,
  onTap,
  size,
  hidden: hiddenProp,
  onHiddenChange,
  paused,
}: {
  mood: PetMood;
  onTap?: () => void;
  size?: number;
  hidden?: boolean;
  onHiddenChange?: (hidden: boolean) => void;
  paused?: boolean;
}) {
  const [internalHidden, setInternalHidden] = usePetHidden();
  const isControlled = hiddenProp !== undefined;
  const hidden = isControlled ? hiddenProp! : internalHidden;
  const setHidden = isControlled ? onHiddenChange! : setInternalHidden;

  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const reducedMotion = useMediaQuery("(prefers-reduced-motion: reduce)");
  const height = size ?? (isDesktop ? 128 : 104);
  const width = Math.round(height * (MOODS.idle.frameW / MOODS.idle.frameH));

  const [hovering, setHovering] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [tipOpen, setTipOpen] = useState(false);
  const [displayMood, setDisplayMood] = useState<PetMood>(mood);
  const [pose, setPose] = useState<PoseState>(() => initialPoseState("right"));

  const floatRef = useRef<HTMLDivElement>(null);
  const poseRef = useRef(pose);
  poseRef.current = pose;
  const posRef = useRef<Pos>({ x: 0, y: 0 });
  const dragOffset = useRef<{ dx: number; dy: number } | null>(null);
  const pointerStart = useRef<{ x: number; y: number } | null>(null);
  const didDrag = useRef(false);
  const tipTimer = useRef<number | null>(null);
  const tipDismiss = useRef<number | null>(null);
  const restTimer = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const phaseStart = useRef<number>(0);
  const wandered = useRef(false);

  const writeFloat = useCallback((x: number, y: number) => {
    posRef.current = { x, y };
    const el = floatRef.current;
    if (el) el.style.transform = `translate3d(${x}px, ${y}px, 0)`;
  }, []);

  // Place once on mount / size change. The FSM owns motion from here on, so the
  // container never carries a CSS transition — that transition was the bug:
  // it slid the pet between two points while the idle sheet played, which read
  // as shaking in place.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const start = readSessionPos() ?? defaultPos(width, height);
    const clamped = clampPos(start.x, start.y, width, height, 16);
    writeFloat(clamped.x, clamped.y);
    setPose((p) => ({ ...p, x: clamped.x, y: clamped.y, targetX: clamped.x, targetY: clamped.y }));
  }, [width, height, writeFloat]);

  useEffect(() => {
    setDisplayMood(mood);
  }, [mood]);

  useEffect(() => {
    const onResize = () => {
      const c = clampPos(posRef.current.x, posRef.current.y, width, height, 16);
      writeFloat(c.x, c.y);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [width, height, writeFloat]);

  useEffect(() => {
    if (hidden || tipAlreadySeen()) return;
    tipTimer.current = window.setTimeout(() => setTipOpen(true), 2000);
    return () => {
      if (tipTimer.current) window.clearTimeout(tipTimer.current);
    };
  }, [hidden]);

  useEffect(() => {
    if (!tipOpen) return;
    tipDismiss.current = window.setTimeout(() => {
      setTipOpen(false);
      markTipSeen();
    }, 5000);
    return () => {
      if (tipDismiss.current) window.clearTimeout(tipDismiss.current);
    };
  }, [tipOpen]);

  const dismissTip = useCallback(() => {
    setTipOpen((open) => {
      if (open) markTipSeen();
      return false;
    });
  }, []);

  // Locomotion loop. The FSM is pure; this effect is the only place that owns a
  // clock, which is what keeps `reducePose` testable with a seeded sweep.
  useEffect(() => {
    if (hidden || reducedMotion || dragging || hovering || typeof window === "undefined") return;
    let alive = true;
    let last = performance.now();

    const scheduleWander = (delayMs: number) => {
      restTimer.current = window.setTimeout(() => {
        if (!alive) return;
        const target = pickWanderTarget(width, height);
        const next = reducePose(
          poseRef.current,
          { type: "startWalk", x: target.x, y: target.y },
          Math.random,
        );
        poseRef.current = next;
        setPose(next);
      }, delayMs);
    };

    // First walk happens sooner than later ones so the pet reads as alive.
    scheduleWander(wandered.current ? 20000 + Math.random() * 25000 : 6000 + Math.random() * 5000);

    const loop = (now: number) => {
      if (!alive) return;
      // Clamp: a backgrounded tab resumes with a huge delta and must not
      // fast-forward the whole walk in one frame.
      const dt = Math.min(64, Math.max(0, now - last));
      last = now;
      const before = poseRef.current;
      let after = reducePose(before, { type: "tick", dtMs: dt }, Math.random);

      // The FSM has no self-timer by design; the component ends the timed
      // one-shots once their sheet has played through.
      if (after.activity !== before.activity) phaseStart.current = now;
      if (after.activity === "turn" && now - phaseStart.current >= TURN_MS) {
        after = reducePose(after, { type: "turnDone" }, Math.random);
        phaseStart.current = now;
      } else if (after.activity === "oneShot" && now - phaseStart.current >= ONE_SHOT_MS) {
        after = reducePose(after, { type: "oneShotEnd" }, Math.random);
        phaseStart.current = now;
      }

      poseRef.current = after;
      if (after.x !== before.x || after.y !== before.y) writeFloat(after.x, after.y);

      if (after.activity === "walk" && before.activity !== "walk") {
        if (restTimer.current) window.clearTimeout(restTimer.current);
      }
      if (before.activity === "walk" && after.activity !== "walk") {
        writeSessionPos({ x: after.x, y: after.y });
        wandered.current = true;
        scheduleWander(20000 + Math.random() * 25000);
      }

      if (
        after.activity !== before.activity ||
        after.frame !== before.frame ||
        after.facing !== before.facing
      ) {
        setPose(after);
      }

      rafRef.current = window.requestAnimationFrame(loop);
    };
    rafRef.current = window.requestAnimationFrame(loop);

    return () => {
      alive = false;
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
      if (restTimer.current) window.clearTimeout(restTimer.current);
    };
  }, [hidden, reducedMotion, dragging, hovering, width, height, writeFloat]);

  const handleWaveEnd = () => {
    if (!hovering) setDisplayMood((m) => (m === "wave" ? "idle" : mood));
  };

  const effectiveMood: PetMood = hovering && !dragging ? "wave" : displayMood;
  const isWalking = pose.activity === "walk" || pose.activity === "turn";

  const sprite = useMemo(() => {
    if (pose.activity === "walk") {
      return (
        <Sprite
          src={WALK.src}
          frames={WALK.frames}
          frameW={WALK.frameW}
          frameH={WALK.frameH}
          cols={WALK.cols}
          frame={pose.frame}
          mirrored={pose.facing === "left"}
          height={height}
          paused={paused && !hovering}
          alt="Study buddy — walking"
          className="pet-sprite"
        />
      );
    }
    if (pose.activity === "turn") {
      return (
        <Sprite
          src={TURN.src}
          frames={TURN.frames}
          frameW={TURN.frameW}
          frameH={TURN.frameH}
          cols={TURN.cols}
          frame={pose.frame}
          mirrored={pose.facing === "left"}
          height={height}
          paused={paused && !hovering}
          alt="Study buddy — turning"
          className="pet-sprite"
        />
      );
    }
    const meta = MOODS[effectiveMood];
    const oneShot = effectiveMood === "wave" || effectiveMood === "celebrate" || effectiveMood === "encourage";
    return (
      <Sprite
        src={meta.src}
        frames={meta.frames}
        frameW={meta.frameW}
        frameH={meta.frameH}
        height={height}
        fps={oneShot ? 5 : 4}
        loop={!oneShot}
        onEnd={oneShot ? handleWaveEnd : undefined}
        paused={paused && !hovering}
        alt={`Study buddy — ${effectiveMood}`}
        className="pet-sprite"
      />
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pose.activity, pose.frame, height, effectiveMood, paused, hovering]);

  const onPointerDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (e.button !== 0) return;
    dismissTip();
    e.currentTarget.setPointerCapture(e.pointerId);
    const cur = posRef.current;
    dragOffset.current = { dx: e.clientX - cur.x, dy: e.clientY - cur.y };
    pointerStart.current = { x: e.clientX, y: e.clientY };
    didDrag.current = false;
    setDragging(true);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!dragOffset.current || !pointerStart.current) return;
    const dist = Math.hypot(e.clientX - pointerStart.current.x, e.clientY - pointerStart.current.y);
    if (dist > 6) didDrag.current = true;
    if (!didDrag.current) return;
    const next = clampPos(e.clientX - dragOffset.current.dx, e.clientY - dragOffset.current.dy, width, height, 8);
    writeFloat(next.x, next.y);
  };

  const endPointer = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!dragOffset.current) return;
    dragOffset.current = null;
    pointerStart.current = null;
    setDragging(false);
    writeSessionPos(posRef.current);
    if (!didDrag.current) {
      markTipSeen();
      setTipOpen(false);
      onTap?.();
    }
    didDrag.current = false;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      /* already released */
    }
  };

  if (hidden) {
    return (
      <button
        className="pet-hidden-toggle"
        onClick={() => setHidden(false)}
        aria-label="Show study assistant"
        title="Show study assistant"
        type="button"
      >
        <Sprite
          src={MOODS.idle.src}
          frames={MOODS.idle.frames}
          frameW={MOODS.idle.frameW}
          frameH={MOODS.idle.frameH}
          height={40}
          paused
          alt="Study buddy icon"
        />
      </button>
    );
  }

  return (
    <div
      ref={floatRef}
      className={`pet-float${hovering ? " is-hover" : ""}${dragging ? " is-dragging" : ""}${reducedMotion ? " is-reduced" : ""}${isWalking ? " is-walking" : ""}`}
      data-pet-float
      data-pet-activity={pose.activity}
      data-pet-facing={pose.facing}
    >
      {tipOpen && (
        <div className="pet-tip" role="status">
          Click me for assistant
        </div>
      )}
      <button
        className="pet-button"
        type="button"
        aria-label="Open study assistant"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endPointer}
        onPointerCancel={endPointer}
        onMouseEnter={() => {
          setHovering(true);
          dismissTip();
        }}
        onMouseLeave={() => setHovering(false)}
        onFocus={() => {
          setHovering(true);
          dismissTip();
        }}
        onBlur={() => setHovering(false)}
        onClick={(e) => e.preventDefault()}
      >
        {sprite}
      </button>
      <button className="pet-hide-link" onClick={() => setHidden(true)} aria-label="Hide study buddy" type="button" tabIndex={-1}>
        Hide
      </button>
    </div>
  );
}
