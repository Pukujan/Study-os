import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Sprite from "./Sprite";

export type PetMood = "idle" | "wave" | "thinking" | "talking" | "celebrate" | "encourage";

const MOODS: Record<PetMood, { src: string; frames: number; frameW: number; frameH: number }> = {
  idle: { src: "/mascot/pet-idle.webp", frames: 6, frameW: 144, frameH: 176 },
  wave: { src: "/mascot/pet-wave.webp", frames: 6, frameW: 144, frameH: 176 },
  thinking: { src: "/mascot/pet-thinking.webp", frames: 6, frameW: 144, frameH: 176 },
  talking: { src: "/mascot/pet-talking.webp", frames: 6, frameW: 144, frameH: 176 },
  celebrate: { src: "/mascot/pet-celebrate.webp", frames: 6, frameW: 144, frameH: 176 },
  encourage: { src: "/mascot/pet-encourage.webp", frames: 6, frameW: 144, frameH: 176 },
};

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

  const [pos, setPos] = useState<Pos>(() => {
    if (typeof window === "undefined") return { x: 0, y: 0 };
    return readSessionPos() ?? defaultPos(width, height);
  });
  const [hovering, setHovering] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [tipOpen, setTipOpen] = useState(false);
  const [displayMood, setDisplayMood] = useState<PetMood>(mood);

  const dragOffset = useRef<{ dx: number; dy: number } | null>(null);
  const pointerStart = useRef<{ x: number; y: number } | null>(null);
  const didDrag = useRef(false);
  const tipTimer = useRef<number | null>(null);
  const tipDismiss = useRef<number | null>(null);
  const wanderTimer = useRef<number | null>(null);
  const posRef = useRef(pos);
  posRef.current = pos;

  useEffect(() => {
    setDisplayMood(mood);
  }, [mood]);

  useEffect(() => {
    const onResize = () => setPos((p) => clampPos(p.x, p.y, width, height, 16));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [width, height]);

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

  useEffect(() => {
    if (hidden || reducedMotion || dragging || hovering) return;
    const tick = () => {
      const next = pickWanderTarget(width, height);
      setPos(next);
      writeSessionPos(next);
      wanderTimer.current = window.setTimeout(tick, 28000 + Math.random() * 22000);
    };
    wanderTimer.current = window.setTimeout(tick, 18000 + Math.random() * 12000);
    return () => {
      if (wanderTimer.current) window.clearTimeout(wanderTimer.current);
    };
  }, [hidden, reducedMotion, dragging, hovering, width, height]);

  const handleWaveEnd = () => {
    if (!hovering) setDisplayMood((m) => (m === "wave" ? "idle" : mood));
  };

  const effectiveMood: PetMood = hovering && !dragging ? "wave" : displayMood;
  const meta = MOODS[effectiveMood];

  const sprite = useMemo(() => {
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
  }, [meta.src, meta.frames, meta.frameW, meta.frameH, height, effectiveMood, paused, hovering]);

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
    setPos(next);
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
      className={`pet-float${hovering ? " is-hover" : ""}${dragging ? " is-dragging" : ""}${reducedMotion ? " is-reduced" : ""}`}
      style={{
        transform: `translate3d(${pos.x}px, ${pos.y}px, 0)`,
        transition: dragging || reducedMotion ? "none" : "transform 4.5s cubic-bezier(0.33, 0, 0.2, 1)",
      }}
      data-pet-float
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
