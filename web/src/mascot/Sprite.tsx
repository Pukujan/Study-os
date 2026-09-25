import { useEffect, useMemo, useState } from "react";

export type SpriteProps = {
  src: string;
  frames: number;
  frameW: number;
  frameH: number;
  height?: number;
  fps?: number;
  loop?: boolean;
  onEnd?: () => void;
  paused?: boolean;
  alt?: string;
  className?: string;
};

export default function Sprite({
  src,
  frames,
  frameW,
  frameH,
  height,
  fps = 12,
  loop = false,
  onEnd,
  paused = false,
  alt = "",
  className,
}: SpriteProps) {
  const [reduced, setReduced] = useState(false);

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

  const ratio = frameW / frameH;
  const h = height ?? frameH;
  const w = Math.round(h * ratio);
  const sheetW = Math.round((frames * frameW * h) / frameH);
  const animName = useMemo(() => `sos-sprite-${frames}-${frameW}-${frameH}-${h}`, [frames, frameW, frameH, h]);
  const isStatic = reduced || paused;
  const duration = frames / fps;

  return (
    <>
      <style>{`
        @keyframes ${animName} {
          from { background-position: 0 0; }
          to { background-position: -${sheetW}px 0; }
        }
      `}</style>
      <div
        role="img"
        aria-label={alt}
        className={className}
        onAnimationEnd={onEnd}
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
          backgroundPosition: "0 0",
          animation: isStatic
            ? undefined
            : `${animName} ${duration}s steps(${frames}) ${loop ? "infinite" : "1"} both`,
          imageRendering: "auto",
          flexShrink: 0,
          overflow: "hidden",
          display: "block",
          boxSizing: "content-box",
        }}
      />
    </>
  );
}
