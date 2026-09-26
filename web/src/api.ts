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
  display_name: string;
  streak_days: number;
  dsa: { current_step: string | null; status: string | null };
  hesi: { sections: Section[]; recommended_topic: string | null; reviews_due: number; content_status: string };
};

export type Me = { handle: string; display_name: string | null; role: string; csrf_token: string };

export type FractionBarFrame = {
  type: "fraction_bar";
  caption?: string;
  bars: { parts: number; shaded: number; label?: string | null; highlight?: number[] | null }[];
  number_line?: { max: number; ticks: number; marks: { at: string; label: string }[] } | null;
};

export type BoxIndexArrow = {
  at: number;
  label: string;
  row: "positions" | "numbers" | "indices";
  dir?: "up" | "down";
};

export type BoxIndexFrame = {
  type: "box_index";
  caption?: string;
  array: number[];
  show_positions: boolean;
  show_indices: boolean;
  box?: { start: number; k: number; brace_label?: string | null } | null;
  arrows?: BoxIndexArrow[] | null;
  circles?: number[];
  sum_label?: string | null;
  interactive?: boolean;
};

export type MermaidFlowFrame = {
  type: "mermaid_flow";
  caption?: string;
  direction?: "TD" | "LR";
  source: string;
  revealed_nodes?: string[];
  zoom_pan?: boolean;
};

export type CodeTreeNode = {
  label: string;
  children?: CodeTreeNode[];
};

export type CodeTreeFrame = {
  type: "code_tree";
  caption?: string;
  language?: string;
  lines: string[];
  highlight?: number[];
  underlines?: { line: number; span: [number, number]; label?: string }[];
  tree?: { label: string; children: CodeTreeNode[] } | null;
};

export type Frame = FractionBarFrame | BoxIndexFrame | MermaidFlowFrame | CodeTreeFrame;

export type Probe = {
  prompt_md: string;
  frames: Frame[];
  answer_kind: "integer" | "fraction" | "choice" | "text";
  choices: string[];
};

export type Feedback = {
  outcome: "correct" | "partial" | "incorrect";
  message_md: string;
  frames: Frame[];
  reassure: boolean;
  sticker: "correct" | "reassure" | null;
  next_action: "continue" | "retry_same";
};

export type WorkedExample = { steps_md: string[] } | { md: string };

export type PlayerView = {
  session_id: string;
  lesson: {
    lesson_id: string;
    revision: string;
    title: string;
    lane: string;
    representation: "fraction_bar" | "box_index";
    total_steps: number;
  };
  step: {
    step_id: string;
    concept_id: string;
    index: number;
    teach_md: string;
    teach_frames: Frame[];
    teach_collapsed: boolean;
    probe: Probe | null;
    variant: number;
  };
  phase: "probe" | "feedback" | "done";
  presentation_version: number;
  presentation_update: PresentationUpdate | null;
  feedback: Feedback | null;
  scaffold: number;
  progress: { done: number; total: number };
  is_guest: boolean;
  card_mode?: "probe" | "worked_example";
  variant_tag?: string | null;
  can_go_back?: boolean;
  worked_example?: WorkedExample;
};

export type PresentationUpdate = {
  schema_version: "study-os.player-presentation.v1";
  operation: "regenerate_presentation";
  lesson_id: string;
  lesson_revision: string;
  step_id: string;
  concept_id: string;
  variant: number;
  phase: "probe" | "feedback";
  card_mode: "probe" | "worked_example";
  scaffold: number;
  previous_version: number;
  version: number;
  teach_md: string;
  teach_frames: Frame[];
  provenance: { prompt_version: string; model: string | null; route: string | null; served: string };
};

export type LanesPayload = {
  continue: {
    lesson_id: string;
    lane: string;
    title: string;
    session_id: string | null;
    label: string;
  };
  lanes: {
    lane_id: string;
    title: string;
    blurb: string;
    status: "available" | "in_progress_content";
    lessons: {
      lesson_id: string;
      title: string;
      state: "not_started" | "in_progress" | "done";
      progress: { done: number; total: number };
    }[];
    legacy: { kind: "hesi_topics" | "dsa_pir"; label: string } | null;
  }[];
};

export type TutorReply = {
  message_id: string;
  reply_md: string;
  prompt_version: string;
  model: string;
  served: "generated" | "fallback";
  suggested_action?: "example" | "easier" | "harder" | "reexplain" | null;
  regenerate_presentation?: PresentationUpdate | null;
};

export type FeedbackReason = "confusing" | "too_long" | "too_easy" | "wrong" | "not_helpful" | "other";

export type TutorMessageFeedbackBody = {
  session_id: string;
  step_id: string;
  target_kind: "tutor_message";
  target_id: string;
  rating: "like" | "dislike";
  reasons: FeedbackReason[];
  free_text?: string;
};

// Learner step review: one explicit Submit of a 1-5 usefulness rating and a
// nonblank typed why, bound to the presentation version the learner reviewed.
export type StepReviewBody = {
  session_id: string;
  step_id: string;
  target_kind: "step";
  target_id: string;
  presentation_version: number;
  rating: number;
  free_text: string;
  idempotency_key: string;
};

export type FeedbackBody = TutorMessageFeedbackBody | StepReviewBody;

export type AdminFeedback = {
  rows: {
    created_at: string;
    rating: string;
    reasons: string[];
    target_kind: string;
    step_id: string | null;
    target_id: string;
    prompt_version: string | null;
    model: string | null;
    free_text_scrubbed: string | null;
    presentation_version: number | null;
  }[];
  by_prompt_version: {
    prompt_version: string;
    likes: number;
    dislikes: number;
    top_reasons: { reason: string; count: number }[];
  }[];
  step_reviews: {
    presentation_version: number | null;
    counts: Record<string, number>;
    total: number;
  }[];
};

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
  claim: async (email: string, passphrase: string) => {
    const me = await post<Me>("/api/auth/claim", { email, passphrase });
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
  // Player v2
  lanes: () => get<LanesPayload>("/api/lanes"),
  tryLesson: (lesson_id?: string) => post<{ me: Me; session: PlayerView }>("/api/try", lesson_id ? { lesson_id } : {}),
  playerStart: (lesson_id: string) => post<PlayerView>("/api/player/sessions", { lesson_id }),
  playerGet: (id: string) => get<PlayerView>(`/api/player/sessions/${id}`),
  playerAttempt: (id: string, response: string, modality: string, idempotency_key: string) =>
    post<PlayerView>(`/api/player/sessions/${id}/attempt`, { response, modality, idempotency_key }),
  playerConfused: (id: string) => post<PlayerView>(`/api/player/sessions/${id}/confused`),
  playerNext: (id: string) => post<PlayerView>(`/api/player/sessions/${id}/next`),
  tutor: (id: string, message: string) => post<TutorReply>(`/api/player/sessions/${id}/tutor`, { message }),
  adapt: (id: string, kind: "example" | "easier" | "harder" | "back") =>
    post<PlayerView>(`/api/player/sessions/${id}/adapt`, { kind }),
  feedback: (body: FeedbackBody) => post<{ ok: boolean; feedback_id: string }>("/api/feedback", body),
  adminFeedback: () => get<AdminFeedback>("/api/admin/feedback"),
};

export function newIdempotencyKey(): string {
  const bytes = new Uint8Array(12);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}
