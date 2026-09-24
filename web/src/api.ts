// Same-origin API client. Every mutation carries X-Study-OS and the CSRF token.

export type Turn = {
  turn_id: string;
  seq: number;
  kind: string;
  markdown: string;
  awaiting: boolean;
  state: string;
  step_id?: string;
  concept?: string;
  phase?: string;
  choices?: string[];
  expansions?: string[];
  outcome?: string;
  generated?: boolean;
  flag?: string;
  summary?: { correct: number; total: number };
};

export type SessionView = {
  session_id: string;
  track: "dsa" | "hesi";
  state: string;
  turns: Turn[];
  topic_id?: string | null;
  resumed?: boolean;
};

export type AttemptResult = { outcome: string; grader?: string; replayed: boolean; turns: Turn[] };

export type Topic = {
  topic_id: string;
  title: string;
  available: boolean;
  state: string;
  prerequisites: string[];
  prerequisites_met: boolean;
};

export type Section = {
  section_id: string;
  exam_id: string;
  title: string;
  topics: Topic[];
  checkpoint_state?: string;
};

export type Home = {
  handle: string;
  display_name: string | null;
  streak_days: number;
  dsa: { current_step: string | null; status: string | null };
  hesi: { sections: Section[]; recommended_topic: string | null; reviews_due: number; content_status: string };
};

export type Me = { handle: string; display_name: string | null; role: string; csrf_token: string };

export class ApiError extends Error {
  constructor(public status: number, public code: string) {
    super(code);
  }
}

let csrfToken: string | null = null;

export function setCsrf(token: string | null): void {
  csrfToken = token;
}

export function getCsrf(): string | null {
  return csrfToken;
}

export function mutationHeaders(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", "X-Study-OS": "1" };
  if (csrfToken) h["X-CSRF-Token"] = csrfToken;
  return h;
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let code = `http_${res.status}`;
    try {
      const body = await res.json();
      code = body.error || body.detail || code;
    } catch {
      /* keep default */
    }
    throw new ApiError(res.status, code);
  }
  return (await res.json()) as T;
}

export async function get<T>(path: string): Promise<T> {
  return parse<T>(await fetch(path, { credentials: "same-origin" }));
}

export async function post<T>(path: string, body: unknown = {}): Promise<T> {
  return parse<T>(
    await fetch(path, { method: "POST", credentials: "same-origin", headers: mutationHeaders(), body: JSON.stringify(body) }),
  );
}

export const api = {
  config: () => get<{ google: boolean; local_signup: boolean }>("/api/auth/config"),
  me: async () => {
    const me = await get<Me>("/api/auth/me");
    setCsrf(me.csrf_token);
    return me;
  },
  signup: async (email: string, passphrase: string) => {
    const me = await post<Me>("/api/auth/signup", { email, passphrase });
    setCsrf(me.csrf_token);
    return me;
  },
  login: async (email: string, passphrase: string) => {
    const me = await post<Me>("/api/auth/login", { email, passphrase });
    setCsrf(me.csrf_token);
    return me;
  },
  logout: () => post<{ ok: boolean }>("/api/auth/logout"),
  home: () => get<Home>("/api/home"),
  start: (body: { track: string; topic_id?: string; checkpoint?: string }) => post<SessionView>("/api/sessions", body),
  session: (id: string) => get<SessionView>(`/api/sessions/${id}`),
  attempt: (id: string, turn_id: string, response: string, idempotency_key: string, latency_ms?: number) =>
    post<AttemptResult>(`/api/sessions/${id}/attempts`, { turn_id, response, idempotency_key, latency_ms }),
  expand: (id: string, turn_id: string, kind: string) =>
    post<AttemptResult>(`/api/sessions/${id}/expansions`, { turn_id, kind }),
  end: (id: string) => post<AttemptResult>(`/api/sessions/${id}/end`),
  summary: (id: string) =>
    get<{ attempts: number; correct: number; next_review_at: string | null; note: string; track: string }>(
      `/api/sessions/${id}/summary`,
    ),
  react: (turn_id: string, kind: string) => post<{ ok: boolean }>(`/api/turns/${turn_id}/reactions`, { kind }),
};

export function newIdempotencyKey(): string {
  const bytes = new Uint8Array(12);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}
