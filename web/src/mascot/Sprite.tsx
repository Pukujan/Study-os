import { useEffect, useRef, useState } from "react";

export type SpriteProps = {
  src: string;
  frames: number;
  frameW: number;
  frameH: number;
  height?: number;
  /** Held-pose fps (JP limited / cutout). Default 3 — slow deliberate loops. */
  fps?: number;
  loop?: boolean;
  onEnd?: () => void;
  paused?: boolean;
  alt?: string;
  className?: string;
  /**
   * Frames per row in the sheet. Defaults to `frames` (a single-row strip),
   * which is the layout every pre-SOS-0014 sheet uses. Multi-row sheets
   * (walk 3x2, turn 2x2) need it to address the grid correctly.
   */
  cols?: number;
  /**
   * Render exactly this frame instead of stepping the sheet. Required for
   * multi-row sheets and for FSM-driven poses, where the caller owns the clock.
   */
  frame?: number;
  /** Mirror horizontally. Sheets are authored facing right. */
  mirrored?: boolean;
};

/**
 * Spritesheet player using **JS-held poses** (discrete frame steps), not CSS
 * @keyframes. Interpolated `background-position` competing with the free-roam
 * transform was the live jitter (A22a / pet_jitter), and keyframes can only
 * walk one axis, so multi-row sheets need the explicit `frame` path anyway.
 */
export default function Sprite({
  src,
  frames,
  frameW,
  frameH,
  height,
  fps = 3,
  loop = false,
  onEnd,
  paused = false,
  alt = "",
  className,
  cols,
  frame,
  mirrored = false,
}: SpriteProps) {
  const [reduced, setReduced] = useState(false);
  const [autoFrame, setAutoFrame] = useState(0);
  const onEndRef = useRef(onEnd);
  onEndRef.current = onEnd;
  const endedRef = useRef(false);
  const controlled = frame !== undefined;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
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

  // Reset to first pose when sheet identity changes.
  useEffect(() => {
    setAutoFrame(0);
    endedRef.current = false;
  }, [src, frames, frameW, frameH]);

  useEffect(() => {
    if (controlled || reduced || paused || frames <= 1) return;
    const safeFps = Math.max(0.5, Math.min(12, fps));
    const holdMs = Math.round(1000 / safeFps);
    const id = window.setInterval(() => {
      setAutoFrame((prev) => {
        if (!loop && endedRef.current) return prev;
        const next = prev + 1;
        if (next >= frames) {
          if (loop) return 0;
          endedRef.current = true;
          onEndRef.current?.();
          return frames - 1;
        }
        return next;
      });
    }, holdMs);
    return () => window.clearInterval(id);
  }, [controlled, reduced, paused, frames, fps, loop, src]);

  const sheetCols = Math.max(1, cols ?? frames);
  const sheetRows = Math.max(1, Math.ceil(frames / sheetCols));
  const ratio = frameW / frameH;
  const h = height ?? frameH;
  const w = Math.round(h * ratio);
  const sheetW = sheetCols * w;
  const sheetH = sheetRows * h;
  const displayFrame = controlled
    ? Math.max(0, Math.min(frames - 1, frame))
    : Math.max(0, Math.min(frames - 1, autoFrame));
  const frameCol = displayFrame % sheetCols;
  const frameRow = Math.floor(displayFrame / sheetCols);

  return (
    <div
      role="img"
      aria-label={alt}
      className={className}
      data-anim="held-pose"
      data-frame={displayFrame}
      data-fps={fps}
      data-frames={frames}
      data-testid="mascot.sprite"
      style={{
        width: `${w}px`,
        height: `${h}px`,
        minWidth: `${w}px`,
        minHeight: `${h}px`,
        maxWidth: `${w}px`,
        maxHeight: `${h}px`,
        backgroundImage: `url("${src}")`,
        backgroundRepeat: "no-repeat",
        backgroundSize: `${sheetW}px ${sheetH}px`,
        backgroundPosition: `${-frameCol * w}px ${-frameRow * h}px`,
        animation: "none",
        imageRendering: "auto",
        flexShrink: 0,
        overflow: "hidden",
        display: "block",
        boxSizing: "content-box",
        transform: mirrored ? "scaleX(-1)" : undefined,
      }}
    />
  );
}
