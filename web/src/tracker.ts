// First-party analytics (D018): batches UX events to POST /api/events (stored in Postgres).
// Never sends free text; only event type, route path, control ids, step ids and durations.

import { mutationHeaders } from "./api";

export type TrackEvent = {
  type:
    | "page_view"
    | "click"
    | "step_shown"
    | "step_answered"
    | "hint_requested"
    | "time_on_step"
    | "idle"
    | "tab_hidden"
    | "tab_visible"
    | "error"
    | "rating";
  path?: string;
  control?: string;
  session_id?: string;
  turn_id?: string;
  step_id?: string;
  value_ms?: number;
  value_int?: number;
  ts?: string;
  client_session?: string;
};

type Sender = (events: TrackEvent[]) => Promise<void> | void;

const PATH_RE = /^\/[A-Za-z0-9/_-]{0,120}$/;
const CONTROL_RE = /^[a-z0-9_.-]{1,48}$/;

export function sanitizePath(path: string): string | undefined {
  const p = path.split("?")[0].split("#")[0];
  return PATH_RE.test(p) ? p : undefined;
}

export function randomId(): string {
  const bytes = new Uint8Array(12);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export class Tracker {
  private queue: TrackEvent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  readonly clientSession: string;
  private stepStartedAt: number | null = null;
  private currentStep: { session_id?: string; turn_id?: string; step_id?: string } = {};

  constructor(
    private send: Sender,
    private opts: { maxBatch?: number; flushMs?: number; now?: () => number } = {},
  ) {
    this.clientSession = randomId();
  }

  private now(): number {
    return this.opts.now ? this.opts.now() : Date.now();
  }

  track(event: TrackEvent): void {
    const e: TrackEvent = { ...event, client_session: this.clientSession, ts: new Date(this.now()).toISOString() };
    if (e.path !== undefined) e.path = sanitizePath(e.path);
    if (e.control !== undefined && !CONTROL_RE.test(e.control)) delete e.control;
    this.queue.push(e);
    if (this.queue.length >= (this.opts.maxBatch ?? 20)) {
      void this.flush();
    } else if (this.timer === null) {
      this.timer = setTimeout(() => void this.flush(), this.opts.flushMs ?? 5000);
    }
  }

  pageView(path: string): void {
    this.track({ type: "page_view", path });
  }

  click(control: string): void {
    this.track({ type: "click", control, path: typeof location !== "undefined" ? location.pathname : undefined });
  }

  stepShown(session_id: string, turn_id: string, step_id?: string): void {
    this.endStep();
    this.currentStep = { session_id, turn_id, step_id };
    this.stepStartedAt = this.now();
    this.track({ type: "step_shown", session_id, turn_id, step_id });
  }

  stepAnswered(): number | undefined {
    const ms = this.stepStartedAt === null ? undefined : this.now() - this.stepStartedAt;
    this.track({ type: "step_answered", ...this.currentStep, value_ms: ms });
    this.endStep();
    return ms;
  }

  hint(kind: string): void {
    this.track({ type: "hint_requested", control: kind, ...this.currentStep });
  }

  endStep(): void {
    if (this.stepStartedAt !== null) {
      this.track({ type: "time_on_step", ...this.currentStep, value_ms: this.now() - this.stepStartedAt });
    }
    this.stepStartedAt = null;
    this.currentStep = {};
  }

  async flush(): Promise<void> {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0, 100);
    try {
      await this.send(batch);
    } catch {
      /* analytics must never break the lesson */
    }
  }
}

export function httpSender(events: TrackEvent[]): Promise<void> {
  return fetch("/api/events", {
    method: "POST",
    credentials: "same-origin",
    headers: mutationHeaders(),
    body: JSON.stringify({ events }),
    keepalive: true,
  }).then(() => undefined);
}

export const tracker = new Tracker(httpSender);

let installed = false;

/** Global listeners: tab visibility, idle, errors, clicks on [data-track] controls. */
export function installGlobalTracking(t: Tracker = tracker, idleMs = 60_000): () => void {
  if (installed || typeof window === "undefined") return () => undefined;
  installed = true;
  let idleTimer: ReturnType<typeof setTimeout> | null = null;
  let idle = false;
  const resetIdle = () => {
    if (idle) idle = false;
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
      idle = true;
      t.track({ type: "idle", value_ms: idleMs, path: location.pathname });
    }, idleMs);
  };
  const onVisibility = () => {
    t.track({ type: document.hidden ? "tab_hidden" : "tab_visible", path: location.pathname });
    if (document.hidden) void t.flush();
  };
  const onClick = (ev: MouseEvent) => {
    const el = (ev.target as HTMLElement | null)?.closest?.("[data-track]");
    if (el) t.click(el.getAttribute("data-track") || "");
    resetIdle();
  };
  const onError = () => t.track({ type: "error", path: location.pathname });
  document.addEventListener("visibilitychange", onVisibility);
  document.addEventListener("click", onClick);
  document.addEventListener("keydown", resetIdle);
  window.addEventListener("error", onError);
  window.addEventListener("unhandledrejection", onError);
  window.addEventListener("pagehide", () => void t.flush());
  resetIdle();
  return () => {
    installed = false;
    if (idleTimer) clearTimeout(idleTimer);
    document.removeEventListener("visibilitychange", onVisibility);
    document.removeEventListener("click", onClick);
    document.removeEventListener("keydown", resetIdle);
    window.removeEventListener("error", onError);
    window.removeEventListener("unhandledrejection", onError);
  };
}
