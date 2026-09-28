/** Thin TTS swap: Kokoro via /api/tts when STUDY_OS_TTS=kokoro, else browser speechSynthesis (Refs #180). */

export type TtsEngine = "browser" | "kokoro";

export type TtsConfig = {
  engine: TtsEngine;
  voice: string | null;
  speed: number | null;
  kokoro: boolean;
};

export type SpeakHandlers = {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: () => void;
  /** Char index for browser speechSynthesis boundary highlighting only. */
  onBoundary?: (charIndex: number, charLength: number) => void;
};

let cachedConfig: TtsConfig | null = null;
let configPromise: Promise<TtsConfig> | null = null;
let currentAudio: HTMLAudioElement | null = null;
let objectUrl: string | null = null;

const BROWSER_FALLBACK: TtsConfig = { engine: "browser", voice: null, speed: null, kokoro: false };

export async function loadTtsConfig(): Promise<TtsConfig> {
  if (cachedConfig) return cachedConfig;
  if (!configPromise) {
    configPromise = fetch("/api/tts/config", { credentials: "same-origin" })
      .then(async (r) => {
        if (!r.ok) return BROWSER_FALLBACK;
        const data = (await r.json()) as Partial<TtsConfig>;
        const engine: TtsEngine = data.engine === "kokoro" ? "kokoro" : "browser";
        const cfg: TtsConfig = {
          engine,
          voice: typeof data.voice === "string" ? data.voice : null,
          speed: typeof data.speed === "number" ? data.speed : null,
          kokoro: engine === "kokoro",
        };
        cachedConfig = cfg;
        return cfg;
      })
      .catch(() => BROWSER_FALLBACK);
  }
  return configPromise;
}

/** For tests. */
export function _resetTtsCache(): void {
  cachedConfig = null;
  configPromise = null;
}

function stopBrowser(): void {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

function stopKokoroAudio(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.src = "";
    currentAudio = null;
  }
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl);
    objectUrl = null;
  }
}

export function cancelSpeak(): void {
  stopBrowser();
  stopKokoroAudio();
}

async function speakKokoro(text: string, handlers: SpeakHandlers): Promise<void> {
  stopKokoroAudio();
  stopBrowser();
  const resp = await fetch("/api/tts/speech", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!resp.ok) {
    // Fall back to browser if Kokoro is down.
    speakBrowser(text, handlers);
    return;
  }
  const blob = await resp.blob();
  objectUrl = URL.createObjectURL(blob);
  const audio = new Audio(objectUrl);
  currentAudio = audio;
  audio.onplay = () => handlers.onStart?.();
  audio.onended = () => {
    handlers.onEnd?.();
    stopKokoroAudio();
  };
  audio.onerror = () => {
    handlers.onError?.();
    stopKokoroAudio();
  };
  try {
    await audio.play();
  } catch {
    handlers.onError?.();
    stopKokoroAudio();
  }
}

function speakBrowser(text: string, handlers: SpeakHandlers): void {
  if (typeof window === "undefined" || !window.speechSynthesis) {
    handlers.onError?.();
    return;
  }
  stopKokoroAudio();
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  if (handlers.onBoundary) {
    utter.onboundary = (e) => handlers.onBoundary?.(e.charIndex, e.charLength);
  }
  utter.onstart = () => handlers.onStart?.();
  utter.onend = () => handlers.onEnd?.();
  utter.onerror = () => handlers.onError?.();
  window.speechSynthesis.speak(utter);
}

/** Speak text with the configured engine (Kokoro when flagged, else browser). */
export async function speakText(text: string, handlers: SpeakHandlers = {}): Promise<void> {
  const trimmed = text.trim();
  if (!trimmed) {
    handlers.onError?.();
    return;
  }
  const cfg = await loadTtsConfig();
  if (cfg.engine === "kokoro") {
    await speakKokoro(trimmed, handlers);
    return;
  }
  speakBrowser(trimmed, handlers);
}

export function browserSpeechAvailable(): boolean {
  return typeof window !== "undefined" && !!window.speechSynthesis;
}
