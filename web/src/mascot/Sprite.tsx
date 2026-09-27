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
};

/**
 * Horizontal spritesheet player using **JS-held poses** (discrete frame steps).
 * No CSS @keyframes — avoids the live "jizzle" when position transforms compete
 * with interpolated background-position (A22a / pet_jitter).
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
}: SpriteProps) {
  const [reduced, setReduced] = useState(false);
  const [frame, setFrame] = useState(0);
  const onEndRef = useRef(onEnd);
  onEndRef.current = onEnd;
  const endedRef = useRef(false);

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
    setFrame(0);
    endedRef.current = false;
  }, [src, frames, frameW, frameH]);

  useEffect(() => {
    if (reduced || paused || frames <= 1) return;
    const safeFps = Math.max(0.5, Math.min(12, fps));
    const holdMs = Math.round(1000 / safeFps);
    const id = window.setInterval(() => {
      setFrame((prev) => {
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
  }, [reduced, paused, frames, fps, loop, src]);

  const ratio = frameW / frameH;
  const h = height ?? frameH;
  const w = Math.round(h * ratio);
  const sheetW = Math.round((frames * frameW * h) / frameH);
  const displayFrame = Math.max(0, Math.min(frames - 1, frame));
  const x = -Math.round(displayFrame * w);

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
        backgroundSize: `${sheetW}px ${h}px`,
        backgroundPosition: `${x}px 0`,
        animation: "none",
        imageRendering: "auto",
        flexShrink: 0,
        overflow: "hidden",
        display: "block",
        boxSizing: "content-box",
      }}
    />
  );
}
