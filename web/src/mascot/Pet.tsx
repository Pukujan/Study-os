import { useEffect, useMemo, useState } from "react";
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

const STORAGE_KEY = "sos.pet.hidden";

export function usePetHidden(initial?: boolean) {
  const [hidden, setHidden] = useState(() => {
    if (typeof window === "undefined") return initial ?? false;
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? stored === "true" : (initial ?? false);
  });
  const setPersisted = (v: boolean) => {
    setHidden(v);
    if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, String(v));
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
  const height = size ?? (isDesktop ? 120 : 96);
  const meta = MOODS[mood];

  const [displayMood, setDisplayMood] = useState<PetMood>(mood);
  useEffect(() => {
    setDisplayMood(mood);
  }, [mood]);

  const handleWaveEnd = () => setDisplayMood("idle");

  const sprite = useMemo(() => {
    const oneShot = displayMood === "wave" || displayMood === "celebrate" || displayMood === "encourage";
    return (
      <Sprite
        src={meta.src}
        frames={meta.frames}
        frameW={meta.frameW}
        frameH={meta.frameH}
        height={height}
        fps={oneShot ? 5 : 8}
        loop={!oneShot}
        onEnd={oneShot ? handleWaveEnd : undefined}
        paused={paused}
        alt={`Study buddy — ${displayMood}`}
      />
    );
  }, [meta, height, displayMood, paused]);

  if (hidden) {
    return (
      <button
        className="pet-hidden-toggle"
        onClick={() => setHidden(false)}
        aria-label="Show study buddy"
        title="Show study buddy"
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
    <div className="pet-wrapper" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.25rem" }}>
      <button
        className="pet-button"
        onClick={onTap}
        aria-label="Open study buddy"
        title="Open study buddy"
        type="button"
      >
        {sprite}
      </button>
      <button
        className="pet-hide-link"
        onClick={() => setHidden(true)}
        aria-label="Hide buddy"
        type="button"
      >
        Hide buddy
      </button>
    </div>
  );
}
