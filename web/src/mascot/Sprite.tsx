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
    // older Safari
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
  const totalW = frames * frameW;
  const animName = useMemo(() => `sos-sprite-${frames}-${frameW}-${frameH}`, [frames, frameW, frameH]);
  const isStatic = reduced || paused;
  const duration = frames / fps;

  return (
    <>
      <style>{`
        @keyframes ${animName} {
          from { background-position-x: 0; }
          to { background-position-x: -${totalW}px; }
        }
      `}</style>
      <div
        role="img"
        aria-label={alt}
        onAnimationEnd={onEnd}
        style={{
          width: `${w}px`,
          height: `${h}px`,
          backgroundImage: `url("${src}")`,
          backgroundRepeat: "no-repeat",
          backgroundSize: "auto 100%",
          backgroundPosition: isStatic ? "0 0" : ("0 0" as React.CSSProperties["backgroundPosition"]),
          animation: isStatic
            ? undefined
            : `${animName} ${duration}s steps(${frames}) ${loop ? "infinite" : "1"} both`,
          imageRendering: "auto",
          flexShrink: 0,
        }}
      />
    </>
  );
}
