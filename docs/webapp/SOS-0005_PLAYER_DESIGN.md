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
11. **Style** (H7 → Alex GO, revised 2026-09-24): canonical characters in `.content-system/characters/` (adult anime **Learner** + robot **Helper**, CGM palette). General art (onboarding, lane cards, empty states, hero, lesson illustrations) = mature anime from the canonical refs. In-app mascot = **chibi Learner as the pet** (see §9); chibi Helper is an idle-only visitor. Real generated images with provenance, never hand-authored SVG substitutes. The pet is never animated during an open assessment probe except for a static idle frame.
12. **Voice** (Alex decision 1, phase 1.5, optional): 🔊 reads teach + prompt via `speechSynthesis`; 🎤 uses `SpeechRecognition`/`webkitSpeechRecognition` when available (note: sends audio to the browser vendor; hidden when unsupported, e.g. Brave). Transcript goes into the answer box; attempt sent with `modality: "voice"`. Server grading cascade: normalised rules (number words, "three quarters" → 3/4) → `semantic_match` hook (MiniLM/bge-small, **disabled stub in this slice**) → Jev when unsure (existing decision layer, later). Open-source STT fallback (transformers.js Whisper/Moonshine, faster-whisper on gravebuster) is documented, not built.

## 1a. Product moat (Alex 2026-09-24)

Study OS's main advantage is not a prettier chat UI. It is:

1. **Multiple forms of information representation for the same idea** — golden-faithful ASCII/box charts rendered as live SVG steppers, Mermaid flow/trees (progressive reveal), code trees, worked examples, and voice/companion — so the learner can switch representation when stuck without leaving the step.
2. **Breaking hard problems into small stepwise pedagogical goals** — one micro-goal per step, produce/predict before being told, fade help, re-explain with a new example on the same representation first, then a different representation if still stuck.

Every design and build choice in this slice must serve that moat: never collapse back into a text-wall + MCQ; never dump a whole concept graph at once; never replace a golden representational diagram with a decorative stand-in. Issue receipts: #101, #107.

## 1b. Binding visual rules (Alex 2026-09-24 — golden + pedagogy transcript; Mermaid-in-lessons refinement)

Issue receipts: #101 (decision + refinement), #107 cross-link. Draft PR #102 — do not merge.

### Concept / stateful diagrams = LIVE steppable golden-faithful SVG (NOT PNG, NOT mermaid for sliding-window)

Goldens (`domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md`, `beginner-sum-enumerate-append.v0.1.md`) are the source of truth for the box/index representation:

1. Monospace-faithful layout rendered as React SVG in `web/src/visuals/` (`BoxIndex`, `FractionBar`, `NumberLine`, `FrameStepper`): index row, positions row, numbers row, ↑/↓ arrows with labels (`i`/`p`/`a`/`k`/`sum`), and a **box brace** `└── box ──┘` under the window (not only a rounded rect overlay).
2. **Arrow / circle visibility (golden rules 4–5):** arrows and circled cells appear ONLY when introducing a concept or explaining/correcting an answer. Exercise / probe diagrams MUST omit arrows and answer-revealing marks. Engine `check_lesson` already asserts no arrows/highlights on probe frames — keep that.
3. **Same chart throughout a concept.** Do not swap representations mid-concept.
4. Make diagrams **interactive** where the golden asks the learner to identify box contents or move the window (tap cells / drag window start; still graded server-side).
5. PNGs are reserved for character art / pet sprites / lane banners only.

Alex tried mermaid for *teaching* the sliding-window concept and rejected it; the ASCII box diagram won. **Do not reintroduce concept-teaching mermaid in place of `BoxIndex`.**

### Mermaid = additional live visual type (progress map + in-lesson flowchart/tree)

Mermaid is easy and cheap to render. Use it for:

1. **Lesson "where am I" progress map** — tiny control-flow / if-then steps; reveal **one node (and its inbound edge) at a time** as the learner completes steps. Never dump the whole concept graph up front (transcript rejection of overloaded mermaid flowcharts).
2. **In-lesson flowchart / tree frames** where a structural diagram helps: relations between concepts, recursion trees, if-then control flow (see `docs/PROJECT_BOUNDARY.md` Structural + Stateful families). Frame type: `mermaid_flow` (see §2). Still reveal progressively via `revealed_nodes` / step progression — not a static wall of nodes.
3. **Responsive layout:** on narrow / mobile viewports use stacked top-down (`TD`/`TB`) graphs; switch to side-by-side / `LR` only when there is horizontal room (desktop). Readable node labels (no tiny text). Tap-to-zoom and pan (reuse the design-bakery `MermaidDiagram` zoom/pan pattern, simplified).

Mermaid never replaces the golden box/array for sliding-window teaching.

### Code blocks = highlightable / expandable trees

DSA code from the enumerate / append / algebra-underlines golden uses a `code_tree` frame: expandable tree or line-highlightable code with underline ranges for the algebraic relation being taught. Not a plain fenced block when the golden shows structure.

### Frame type summary

| `type` | Use | Not for |
|---|---|---|
| `box_index` | Sliding-window / array+window goldens (LIVE SVG) | Replacing with mermaid or PNG |
| `fraction_bar` (+ optional `number_line`) | HESI fractions | Decorative only |
| `mermaid_flow` | Progress map; in-lesson flowchart/tree with progressive reveal | Teaching the sliding-window box itself |
| `code_tree` | Enumerate / append / algebra underlines | Dumping whole files |

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

`Frame` (rendered by the client; text form also rendered server-side for tutor grounding). Types serve the moat (§1a): switch representation, never a text wall.

```jsonc
// fraction_bar
{ "type": "fraction_bar", "caption": "optional ≤ 12 words",
  "bars": [{ "parts": 4, "shaded": 3, "label": "3/4 | null", "highlight": [0,1,2] }],   // highlight = explain/intro only
  "number_line": { "max": 1, "ticks": 12, "marks": [{ "at": "3/4", "label": "3/4" }] } | null }
// box_index — golden ASCII box/array as LIVE SVG (NOT mermaid, NOT PNG). Brace + arrow rules in §1b.
{ "type": "box_index", "caption": "...",
  "array": [4, 7, 2, 6, 1, 9], "show_positions": true, "show_indices": false,
  "box": { "start": 1, "k": 3, "brace_label": "box | k = 3 | null" } | null,  // start = index i (0-based); brace under numbers
  "arrows": [{ "at": 2, "label": "p = 3", "row": "positions|numbers|indices", "dir": "down|up" }],  // intro/explain only
  "circles": [2, 3],                         // circled cells; intro/explain only
  "sum_label": "sum[i=2] = 9 | null",
  "interactive": false }                     // true when learner may tap cells / move window
// mermaid_flow — progress map OR in-lesson flowchart/tree (PROJECT_BOUNDARY Structural). Progressive reveal.
{ "type": "mermaid_flow", "caption": "...",
  "direction": "TD",                         // TD default; client may flip TD↔LR by viewport width
  "source": "flowchart TD\n  A[Ready?] --> B[Position p]",
  "revealed_nodes": ["A", "B"],              // only these nodes (+ inbound edges) render; rest hidden
  "zoom_pan": true }
// code_tree — enumerate / append / algebra underlines from DSA goldens
{ "type": "code_tree", "caption": "...",
  "language": "python",
  "lines": ["S = []", "for i, num in enumerate(a):", "    S.append(num)"],
  "highlight": [1, 2],                       // 0-based line indexes
  "underlines": [{ "line": 2, "span": [4, 16], "label": "same expression" }],
  "tree": { "label": "enumerate(a)", "children": [{ "label": "(i, num)", "children": [] }] } | null }
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
| POST | `/api/player/sessions/{id}/tutor` | `{message}` (≤ 500 chars) | `{message_id, reply_md, prompt_version, model, served: "generated"|"fallback", suggested_action: "example"|"easier"|"harder"|"reexplain"|null}` (the client renders the suggestion as a button; the server never auto-applies it) |
| POST | `/api/player/sessions/{id}/adapt` | `{kind: "example"|"easier"|"harder"|"back"}` | `PlayerView` — updates the question card **in place** (`card_mode: "probe"|"worked_example"`, `variant_tag: "easier"|"harder"|null`, `can_go_back`); refused (no change) during an assessment probe |
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

Routes: `/` (signed-in Home lanes; signed-out Try picker), `/try` alias, `/play/:session_id` (Player), `/admin/feedback`, existing `/login`, `/lesson/:id`, `/summary/:id` kept. Components: `visuals/FractionBar.tsx`, `visuals/NumberLine.tsx`, `visuals/BoxIndex.tsx` (golden brace/arrows/circles), `visuals/MermaidDiagram.tsx` (zoom/pan, TD↔LR by viewport, progressive `revealed_nodes`), `visuals/LessonMap.tsx` (tiny where-am-I mermaid), `visuals/CodeTree.tsx`, `visuals/FrameStepper.tsx` (Back/Next, "Step 2 of 3"), `player/CompanionPanel.tsx` (replaces the drawer TutorPanel: half-height bottom sheet on mobile, non-dimming side panel ≥ 1024 px; see §9), `mascot/Pet.tsx` + `mascot/RobotVisit.tsx`, `player/FeedbackBar.tsx` (👍/👎 + reasons popover), `player/VoiceControls.tsx` Layout: single column ≤ 720 px content width; one primary button per screen; 16 px base font; WCAG AA contrast.

## 7. Evals (`tools/run_tutor_golden_evals.py`)

Golden situations are generated from every probe of every lesson × personas: `asks_for_answer`, `wrong_then_confused`, `partial`, `off_topic`, `prompt_injection`, `correct_wants_why`. Each is replayed against each tutor prompt version (v1, v2) through the real tutor module (InferHub `cb/glm-5.3`, fallback `cb/deepseek-v4.1-flash`, or a stub with `--offline`). Graded by the oracle rules: `no_leak`, `one_question`, `word_budget`, `no_mastery`, `grounded` (mentions a representation term of the step), `acknowledges_partial` (partial persona), `stays_on_step` (off-topic/injection persona redirects). Engine conformance (deterministic) replays the golden flows: correct → why → advance; wrong → answer + why + reassure → different example → check → advance; partial → acknowledge. Output: `docs/webapp/evals/tutor-golden-<date>.json` + markdown summary with pass rates per prompt version, cost and routes.

## 9. Companion: one screen, one shared state (Alex 2026-09-24, H14/H15)

- **Pet** = chibi Learner sprite (`web/public/mascot/pet-*.webp`), docked bottom-right of the player (≤ 96 px mobile / 120 px desktop tall), never covering the question card. States: `idle` (breathe/blink/fidget, default), `wave` (session start / panel open), `thinking` (tutor request in flight), `talking` (TTS speaking or reply streaming; speech bubble shows the live transcript), `celebrate` (correct, once), `encourage` (incorrect/confused, once). Mute/hide toggle persists in localStorage. `prefers-reduced-motion`: first frame only, no robot visits.
- **Tap the pet** → companion panel expands; the **question/visual card stays visible** (mobile: half-height bottom sheet over the lower half, card scrolls above it; desktop: side panel, no page dimming). Panel = transcript bubbles, text box, mic toggle (STT) and speaker toggle (TTS). Voice is an input/output toggle inside the panel, not a separate mode or chatbot.
- **Card-in-place actions** from the panel (buttons + tutor `suggested_action`): *Show a worked example* (same frames, card_mode worked_example), *Easier*, *Harder* (variants per fading), *Explain again* (confused → new example on the same representation). The card updates in place with a small `variant` / `worked example` tag and a **Back** control; nothing of this is rendered inside the chat.
- **Collapse** → plain view; progress, card state and chat history are kept (history is per session in client state and reloaded from the tutor log on resume).
- Guarded: answers stay server-side, tutor validation (no leak while probe open), adapt refused during assessment probes, same decision cascade and logging (`learn.player_event` kind `adapt`, `learn.llm_interaction` for every tutor call).
- **Robot visit** (chibi Helper, supporting character): after ≥ 90 s idle, at most once per 10 min, ≤ 6 s: `robot-hover` slides in → one pass of `duo-headpat` or `duo-starplay` → slides out. Never during an assessment probe, while typing/speaking, while the pet is talking/thinking/reacting, or under reduced motion / mascot hidden. Rules in `.content-system/characters/characters.json#robot_visit`.

## 8. Non-goals in this slice

Semantic-embedding grading (hook only), transformers.js/faster-whisper STT, bandits, FSRS integration of player lessons, Google sign-in for claim, deploy.
