import { useEffect, useState } from "react";

const EVENTS = ["pointerdown", "keydown", "input", "touchstart", "click", "scroll"];

export function useIdle(minIdleMs: number, enabled: boolean): boolean {
  const [idle, setIdle] = useState(false);
  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    let timer = window.setTimeout(() => setIdle(true), minIdleMs);
    const reset = () => {
      setIdle(false);
      clearTimeout(timer);
      timer = window.setTimeout(() => setIdle(true), minIdleMs);
    };
    EVENTS.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    return () => {
      clearTimeout(timer);
      EVENTS.forEach((e) => window.removeEventListener(e, reset));
    };
  }, [minIdleMs, enabled]);
  return idle;
}
