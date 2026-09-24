# SOS-0005 Lesson player v2 — design and contracts

Issue log: #101 (player), #103 (style), #104 (try-first), #105 (lanes), #106 (voice), research gate #107 (Alex decisions 2026-09-24). Draft PR #102 — do not merge.

Evidence mapping (see `docs/research/sos-0005-evidence-review.md`): each rule below cites the hypothesis verdict it applies.

## 1. Principles (binding)

1. **One concept per step; learner produces before being told** (H1). Each step = optional short teach (≤ 40 words) + one probe.
2. **Fading** (H1, expertise reversal): `scaffold` level 0–2 per session. Two first-try correct answers in a row → scaffold+1 (teach frames collapsed behind "Show me again", intro-only steps marked `skippable` are skipped). Any incorrect → scaffold−1 (teach frames shown again).
3. **Golden feedback flow** (goldens rules 6–8, oracle `feedback_required/fix_required/partial_required`):
   - correct → "Correct — **X**." + why on the *same* visual (explain frame) → advance (or one confirm variant when `confirm: true`).
   - incorrect → give the right answer, show why on the same visual, reassure ("That's okay — this one trips people up.") → retry with a **different example (variant), same representation** → if correct → **one more** different example (check) → advance. Incorrect again → smaller step: show the teach frames again + next variant (never loop forever: after 3 misses on a step, advance with status `needs_review`).
   - partial (answer matches a `partial` pattern) → acknowledge the correct part, isolate what is missing, same probe again.
4. **Visuals are representational and learner-stepped** (H2). Frames advance only on learner action ("Next"), never auto-play. Probe frames never contain answer-revealing arrows/highlights (golden rule 5; engine asserts it).
5. **Re-explain = new example, same representation first** (H4). "I'm confused" → deterministic: explain frames + next variant. No LLM needed.
6. **Guarded tutor chat** (H3, H12): grounded in the step (teach, visual as text, probe, canonical solution, golden rules); the accepted answers are server-side only; replies validated (`validator.validate_generated`, answer leak while the probe is open, ≤ 1 question, word budget 90, no mastery claims); one repair retry, then deterministic fallback hint. Versioned prompts in `src/study_os/web/player/prompts/tutor.vN.md`. Every LLM call is logged to `learn.llm_interaction`.
7. **Reduced motion** (H6): all transitions ≤ 200 ms, disabled under `prefers-reduced-motion: reduce`; no autoplay anywhere.
8. **Home** (H9, H10): one screen, all four lanes (DSA, HESI, AI from scratch, Study OS), one primary **Continue** action, no carousel/hero banner/row scrolling. Lanes without lessons are visible and say "First lesson in progress" (disabled), never hidden.
9. **Try before signup, no tutorial screens** (H8): signed-out `/` shows the lane picker; "Try a lesson — no account needed" starts a guest session immediately; the "Save your progress" prompt appears at the end of the first lesson.
10. **Feedback everywhere** (Alex decision 3): like / dislike on every step view and every tutor message; on dislike, quick reasons `confusing | too_long | too_easy | wrong | not_helpful | other` + optional free text (≤ 500 chars, PII-scrubbed). Stored with prompt version, model, step, session.
11. **Style** (H7 → Alex GO): grown-up anime/sticker mascot, used only on feedback moments (correct / reassure / lesson done) and home header, **never on probe screens**. Assets via CGM `.content-system/` with provenance.
12. **Voice** (Alex decision 1, phase 1.5, optional): 🔊 reads teach + prompt via `speechSynthesis`; 🎤 uses `SpeechRecognition`/`webkitSpeechRecognition` when available (note: sends audio to the browser vendor; hidden when unsupported, e.g. Brave). Transcript goes into the answer box; attempt sent with `modality: "voice"`. Server grading cascade: normalised rules (number words, "three quarters" → 3/4) → `semantic_match` hook (MiniLM/bge-small, **disabled stub in this slice**) → Jev when unsure (existing decision layer, later). Open-source STT fallback (transformers.js Whisper/Moonshine, faster-whisper on gravebuster) is documented, not built.

## 2. Lesson content schema (`study-os.player-lesson.v1`)

Files: `src/study_os/web/player/lessons/<lesson_id>.v1.json`.

```jsonc
{
  "schema_version": "study-os.player-lesson.v1",
  "lesson_id": "fractions-compare",          // [a-z0-9-]+
  "revision": "fractions-compare.v1",
  "lane": "hesi",                             // dsa | hesi | ai-from-scratch | study-os
  "title": "Comparing fractions",
  "summary": "Which is bigger, 3/4 or 2/3? Find out with fraction bars.",
  "representation": "fraction_bar",          // fraction_bar | box_index
  "golden_ref": "path or 'derived-from-goldens-rules'",
  "steps": [
    {
      "step_id": "denominator",
      "kc": "fraction.denominator",
      "skippable": false,                     // intro-only steps may be skipped when scaffold >= 1
      "confirm": false,                       // ask one confirm variant even after first-try correct
      "teach": { "md": "≤40 words", "frames": [Frame, ...] },   // frames may be []
      "probe": Probe | null,                  // null only for the problem-statement step ("Ready?")
      "variants": [ { "teach_frames": [Frame], "probe": Probe }, ... ]   // ≥2 per probe step; same representation, different numbers
    }
  ]
}
```

`Probe`:

```jsonc
{
  "prompt_md": "What fraction of the bar is shaded?",
  "frames": [Frame],                          // exercise visual; MUST NOT contain arrows/highlight marks
  "answer_kind": "integer | fraction | choice | text",
  "choices": ["3/4", "2/3"],                 // only for choice
  "accept": ["3/4", "0.75"],                 // server-only
  "partial": [{ "match": ["3"], "note_md": "Yes, 3 parts are shaded. Now out of how many?" }],
  "misconceptions": [{ "id": "bigger-denominator-bigger", "match": ["1/4"], "note_md": "..." }],
  "correct_md": "Correct — **3/4**.",
  "explain_md": "why, referring to the same picture (≤ 50 words)",
  "explain_frames": [Frame],                  // same representation, arrows allowed
  "solution_md": "canonical worked solution (server-only; tutor grounding)",
  "hint_md": "deterministic fallback hint that does not contain the answer"
}
```

`Frame` (rendered by the client as SVG; the text form is also rendered server-side for tutor grounding):

```jsonc
// fraction_bar
{ "type": "fraction_bar", "caption": "optional ≤ 12 words",
  "bars": [{ "parts": 4, "shaded": 3, "label": "3/4 | null", "highlight": [0,1,2] }],   // highlight = explain/intro only
  "number_line": { "max": 1, "ticks": 12, "marks": [{ "at": "3/4", "label": "3/4" }] } | null }
// box_index (mirrors PIR sliding-window diagrams)
{ "type": "box_index", "caption": "...",
  "array": [4, 7, 2, 6, 1, 9], "show_positions": true, "show_indices": false,
  "box": { "start": 1, "k": 3 } | null,       // start is an index i (0-based)
  "arrows": [{ "at": 2, "label": "p = 3", "row": "positions|numbers" }],   // intro/explain only
  "sum_label": "sum[1] = 15 | null" }
```

Answer normalisation (grading.py): trim, lowercase, strip trailing `.`, unicode minus, `½ ¼ ¾` → `1/2 1/4 3/4`; fractions compared by value only when `answer_kind == "fraction"` **and** the accept list is value-based (e.g. `6/8` counts as correct for `3/4` with note "same amount — 3/4 is the simplest name"); integer words zero–twenty → digits; voice phrases: "three quarters/fourths" → 3/4, "two thirds" → 2/3, "one half" → 1/2, "x over y" / "x out of y" → x/y.

## 3. Engine (pure, `src/study_os/web/player/engine.py`)

- `start(lesson) -> State`; `view(lesson, state) -> dict` (public, never contains `accept`, `partial.match`, `misconceptions.match`, `solution_md`, `hint_md` except via the fallback path); `attempt(lesson, state, response, modality) -> (State, Feedback)`; `confused(lesson, state) -> (State, Feedback)`; `next(lesson, state) -> State` (acknowledge feedback / continue).
- State (JSON-serialisable): `{step_index, variant_index (-1 = main probe), phase: "probe"|"feedback"|"done", pending: "retry"|"check"|null, misses_on_step, first_try_streak, scaffold, history: [{step_id, variant, outcome, modality}], status_by_step}`.
- Feedback: `{outcome: correct|partial|incorrect, message_md, frames, reassure: bool, sticker: "correct"|"reassure"|null, next_action: "continue"|"retry_same"}`.
- `engine.check_lesson(lesson)` validates the schema and golden rules: every probe step has ≥ 2 variants; probe frames contain no arrows/highlight; teach ≤ 40 words; explain ≤ 50 words; ≤ 1 `?` in prompt; one `kc` per step. Tests run it on every lesson file.

## 4. API (FastAPI, same app; CSRF/cookie rules as existing)

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/lanes` | – | `{continue: {lesson_id, lane, title, session_id|null, label} , lanes: [{lane_id, title, blurb, status: "available"|"in_progress_content", lessons: [{lesson_id, title, state: not_started|in_progress|done, progress: {done, total}}], legacy: {kind: "hesi_topics"|"dsa_pir", label}|null}]}` |
| POST | `/api/try` | `{lesson_id?}` | signed-out only: creates guest account (`auth.account.is_guest = true`, handle `guest-<8hex>`), sets session cookie, starts a player session; returns `{me, session: PlayerView}` |
| POST | `/api/auth/claim` | `{email, passphrase}` | guest → local account (keeps subject and progress); returns `me` |
| POST | `/api/player/sessions` | `{lesson_id}` | `PlayerView` (resumes an unfinished session for the same lesson) |
| GET | `/api/player/sessions/{id}` | – | `PlayerView` |
| POST | `/api/player/sessions/{id}/attempt` | `{response, modality: "text"|"voice"|"choice", idempotency_key}` | `PlayerView` (with `feedback`) |
| POST | `/api/player/sessions/{id}/confused` | – | `PlayerView` (new example, same representation) |
| POST | `/api/player/sessions/{id}/next` | – | `PlayerView` |
| POST | `/api/player/sessions/{id}/tutor` | `{message}` (≤ 500 chars) | `{message_id, reply_md, prompt_version, model, served: "generated"|"fallback"}` |
| POST | `/api/feedback` | `{session_id, step_id, target_kind: "step"|"tutor_message", target_id, rating: "like"|"dislike", reasons: [...], free_text?}` | `{ok, feedback_id}` |
| GET | `/api/admin/feedback` | – (role admin) | `{rows: [...latest 200], by_prompt_version: [{prompt_version, likes, dislikes, top_reasons}]}` |

`PlayerView = {session_id, lesson: {lesson_id, title, lane, representation, total_steps}, step: {step_id, index, teach_md, teach_frames, teach_collapsed: bool, probe: {prompt_md, frames, answer_kind, choices} | null, variant: int}, phase, feedback: Feedback | null, scaffold, progress: {done, total}, is_guest: bool}`.

HESI-only bug (#105): root cause is that `home()` and `Home.tsx` hard-code HESI + one DSA card and there is no lane registry; Study OS and AI-from-scratch have no entry at all. Fix: `player/lanes.py` registry with all four lanes; `/api/lanes` built from the registry + lesson files + progress. Legacy HESI topics and the legacy DSA PIR lesson stay reachable from their lanes.

## 5. Data (migration `0002_player.sql`)

- `auth.account.is_guest boolean NOT NULL DEFAULT false`.
- `learn.player_session(session_id uuid PK, subject_id uuid FK learn.subject, lesson_id text, lesson_revision text, state jsonb, started_at, updated_at, ended_at NULL)`.
- `learn.player_event(id bigserial PK, session_id FK, seq int, step_id text, event text, modality text NULL, outcome text NULL, response_scrubbed text NULL, idempotency_key text UNIQUE NULL, payload jsonb, created_at)` — append-only (same trigger pattern as `learn.attempt`).
- `learn.llm_interaction(id uuid PK, session_id uuid NULL, step_id text NULL, operation text, prompt_id text, prompt_version text, route text, model text, messages jsonb (scrubbed), response_text text, served text, tokens_in, tokens_out, cost_usd numeric(12,8), latency_ms, validation_codes text[], created_at)` — append-only.
- `ux.feedback(feedback_id uuid PK, subject_id uuid, session_id uuid NULL, step_id text NULL, target_kind text, target_id text, rating text, reasons text[], free_text_scrubbed text NULL, prompt_version text NULL, model text NULL, llm_interaction_id uuid NULL, created_at)`.
- `analytics.v_feedback` (Metabase-ready): feedback joined with llm_interaction (prompt_version, model, route) and lesson/step.
- Update `tests/test_web_api.py::EXPECTED_TABLES`.

## 6. Client (`web/src`)

Routes: `/` (signed-in Home lanes; signed-out Try picker), `/try` alias, `/play/:session_id` (Player), `/admin/feedback`, existing `/login`, `/lesson/:id`, `/summary/:id` kept. Components: `visuals/FractionBar.tsx`, `visuals/NumberLine.tsx`, `visuals/BoxIndex.tsx`, `visuals/FrameStepper.tsx` (Back/Next, "Step 2 of 3"), `player/TutorPanel.tsx` (drawer on mobile, side panel ≥ 1024 px), `player/FeedbackBar.tsx` (👍/👎 + reasons popover), `player/VoiceControls.tsx`, `Sticker.tsx`. Layout: single column ≤ 720 px content width; one primary button per screen; 16 px base font; WCAG AA contrast.

## 7. Evals (`tools/run_tutor_golden_evals.py`)

Golden situations are generated from every probe of every lesson × personas: `asks_for_answer`, `wrong_then_confused`, `partial`, `off_topic`, `prompt_injection`, `correct_wants_why`. Each is replayed against each tutor prompt version (v1, v2) through the real tutor module (InferHub `cb/glm-5.3`, fallback `cb/deepseek-v4.1-flash`, or a stub with `--offline`). Graded by the oracle rules: `no_leak`, `one_question`, `word_budget`, `no_mastery`, `grounded` (mentions a representation term of the step), `acknowledges_partial` (partial persona), `stays_on_step` (off-topic/injection persona redirects). Engine conformance (deterministic) replays the golden flows: correct → why → advance; wrong → answer + why + reassure → different example → check → advance; partial → acknowledge. Output: `docs/webapp/evals/tutor-golden-<date>.json` + markdown summary with pass rates per prompt version, cost and routes.

## 8. Non-goals in this slice

Semantic-embedding grading (hook only), transformers.js/faster-whisper STT, bandits, FSRS integration of player lessons, Google sign-in for claim, deploy.
