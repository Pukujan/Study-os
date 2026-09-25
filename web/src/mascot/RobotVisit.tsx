import { useEffect, useRef, useState } from "react";
import { useIdle } from "./useIdle";
import { shouldVisit, type VisitContext } from "./visitRules";
import Sprite from "./Sprite";

declare global {
  interface Window {
    __SOS_FORCE_ROBOT_VISIT__?: boolean;
  }
}

const DUOS = [
  { src: "/mascot/duo-headpat.webp", frames: 9, frameW: 216, frameH: 144 },
  { src: "/mascot/duo-starplay.webp", frames: 9, frameW: 216, frameH: 144 },
] as const;

const STORAGE_KEY = "sos.robot.lastVisit";
const ACTIVITY_EVENTS = ["pointerdown", "keydown", "input", "touchstart", "click", "scroll"];

function getLastVisit(): number | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isNaN(n) ? null : n;
}

function setLastVisit(now: number): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, String(now));
}

export type RobotVisitProps = {
  petHidden: boolean;
  probeOpen: boolean;
  typing: boolean;
  speaking: boolean;
  petTalking: boolean;
  petThinking: boolean;
};

export default function RobotVisit({
  petHidden,
  probeOpen,
  typing,
  speaking,
  petTalking,
  petThinking,
}: RobotVisitProps) {
  const [reducedMotion, setReducedMotion] = useState(false);
  const [phase, setPhase] = useState<"idle" | "entering" | "playing" | "exiting">("idle");
  const [duoIndex, setDuoIndex] = useState(0);
  const lastVisitRef = useRef<number | null>(getLastVisit());
  const timersRef = useRef<number[]>([]);
  const idle = useIdle(90000, phase === "idle");
  const forced = typeof window !== "undefined" && !!window.__SOS_FORCE_ROBOT_VISIT__;

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
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
  }, []);

  // Cancel the visit on any user input.
  useEffect(() => {
    if (phase === "idle") return;
    const cancel = () => {
      timersRef.current.forEach((t) => clearTimeout(t));
      timersRef.current = [];
      setPhase("idle");
    };
    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, cancel, { passive: true }));
    return () => ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, cancel));
  }, [phase]);

  useEffect(() => {
    if (phase !== "idle") return;
    const lastSeconds = lastVisitRef.current ? Math.max(0, (Date.now() - lastVisitRef.current) / 1000) : null;
    const ctx: VisitContext = {
      idleSeconds: forced ? 91 : idle ? 91 : 0,
      lastVisitSeconds: lastSeconds,
      probeOpen,
      typing,
      speaking,
      petTalking,
      petThinking,
      reducedMotion,
      petHidden,
    };
    if (!shouldVisit(ctx)) return;

    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
    const push = (fn: () => void, ms: number) => timersRef.current.push(window.setTimeout(fn, ms));

    const run = () => {
      lastVisitRef.current = Date.now();
      setLastVisit(lastVisitRef.current);
      setDuoIndex(Math.floor(Math.random() * DUOS.length));
      setPhase("entering");
      push(() => setPhase("playing"), 1200);
      push(() => setPhase("exiting"), 3000);
      push(() => setPhase("idle"), 4200);
    };

    if (forced) {
      push(run, 1000);
    } else {
      run();
    }

    return () => timersRef.current.forEach((t) => clearTimeout(t));
  }, [idle, phase, forced, petHidden, probeOpen, typing, speaking, petTalking, petThinking, reducedMotion]);

  if (phase === "idle") return null;

  const duo = DUOS[duoIndex];
  const scale = 1.3;

  return (
    <div className={`robot-visit phase-${phase}`} aria-hidden>
      <div className="robot-duo">
        <Sprite
          src={duo.src}
          frames={duo.frames}
          frameW={duo.frameW}
          frameH={duo.frameH}
          height={Math.round(120 * scale)}
          fps={8}
          loop={false}
          alt="Robot visit"
        />
      </div>
    </div>
  );
}
