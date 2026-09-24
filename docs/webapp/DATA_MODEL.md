# Data model

Postgres 16 on gravebuster. Semantics follow [`docs/DATABASE_CONTRACT.md`](../DATABASE_CONTRACT.md) and [`docs/MEASUREMENT_MODEL.md`](../MEASUREMENT_MODEL.md). Column lists are normative for **personal-data scope** (a schema allowlist test enforces them). Other column names may be refined in the implementing task (#87).

## 1. Schemas and roles

| Schema | Contents | Writable by | Readable by |
|---|---|---|---|
| `auth` | accounts, sessions, invites | `app` | `app` |
| `learn` | subjects, content revisions, sessions, turns, attempts, capability transitions, interpretations, generations | `app` (INSERT only on event tables) | `app`, `analytics` (via views) |
| `ux` | reactions, timing, lifecycle events | `app` (INSERT only) | `app`, `analytics` (via views) |
| `memory` | learner-memory records (derived, mutable projection) | `app` | `app` |
| `analytics` | views only | migration owner | `analytics` role (Metabase, DuckDB) |

## 2. Core tables

```text
auth.account(account_id uuid pk, handle citext unique, passphrase_hash text, role text check in ('learner','admin'),
             created_at timestamptz, disabled_at timestamptz null)
auth.session(session_id_hash bytea pk, account_id fk, created_at, last_seen_at, expires_at, revoked_at null)
auth.invite(code_hash bytea pk, created_by fk, created_at, redeemed_at null, role text)
auth.account_subject(account_id fk unique, subject_id uuid unique)      -- the only bridge; learn.* never joins auth.*

learn.subject(subject_id uuid pk, created_at, pseudonym text)           -- e.g. 'subject-002'; no real names
learn.content_revision(revision_id pk, kind in ('pir_asset','subject_pack'), ref text, sha256 text, created_at)
learn.kc(kc_id text pk, domain text, title text, prerequisites text[])  -- e.g. 'dsa.sliding_window.sum_i', 'hesi.priority.abc'
learn.item(item_id text pk, kc_id fk, revision_id fk, item_type, role in ('teach','check','transfer','holdout'),
           license text not null, source text not null)
learn.session(session_id uuid pk, subject_id fk, started_at, ended_at null, end_state text null,
              module_version_set jsonb not null)
learn.turn(turn_id uuid pk, session_id fk, seq int, state_before text, event text, state_after text,
           step_id text, item_id text null, assistance_level smallint check 0..6, representation_id text,
           operation text, served_from in ('canonical','promoted','generated','fallback'),
           controller_revision text, created_at)                      -- append-only
learn.attempt(attempt_id uuid pk, turn_id fk, idempotency_key text unique, response_kind text,
              response_text_scrubbed text, grader in ('deterministic','interpreter'), outcome text,
              latency_ms int, evidence_class text default 'observed', created_at)   -- append-only
learn.capability_transition(id pk, subject_id, kc_id, from_state, to_state, evidence_attempt_ids uuid[],
              assistance_level, window in ('immediate','faded','transfer','delayed'), created_at)  -- append-only
learn.interpretation(id pk, turn_id fk, operation text, route text, model text, price_snapshot_id text,
              prompt_template_version text, input_tokens int, output_tokens int, cost_usd numeric(12,8),
              latency_ms int, validation_result text, violation_codes text[], created_at)   -- no prompt text
learn.generation(generation_id pk, interpretation_id fk, step_id, content_json jsonb, validated bool,
              next_check_outcome text null, promotion_state in ('none','candidate','approved','rejected','promoted'),
              promoted_revision_id null)
learn.review_schedule(subject_id, kc_id or item_id, fsrs_state jsonb, due_at, updated_at)   -- projection
```

`response_text_scrubbed`: the free-text answer after the PII scrubber (#95). Numeric/choice answers are stored as-is. Raw pre-scrub text is **never** persisted.

## 3. UX signals (sentiment, frustration, what works)

| Signal | Source | Class | Table |
|---|---|---|---|
| Reaction after feedback: `helped` / `confused` / `frustrated` / `too_easy` | one tap, optional | self_reported | `ux.reaction(turn_id, kind, created_at)` |
| Perceived difficulty 1–5 at step end (sampled, ≤1 prompt / 5 steps) | tap | self_reported | `ux.rating` |
| Time to first input, time to submit, idle gaps > 60 s | client timing (coarse, rounded to 100 ms) | observed | `ux.timing` |
| Hint requests, "explain differently" requests, retries | API | observed | derived from `learn.turn` |
| Abandon (tab hidden > 10 min mid-step / no resume in 24 h) | client lifecycle + server | observed | `ux.lifecycle` |
| Frustration index = f(consecutive incorrect, rapid resubmits < 2 s, `frustrated` taps, abandon after correction) | computed | derived (versioned formula) | `analytics.v_friction` |
| What works = next-check unaided correct rate by `operation × representation × served_from` | computed | derived | `analytics.v_operation_effect` |

Not collected: keystrokes, mouse paths, session replay, IP, user agent, geolocation, device fingerprint, and free-text feedback, unless the learner opts in per message and it passes the scrubber.

## 4. Learner memory: schema and scope rules

Purpose: give the controller and interpreter compact, evidence-backed context **about learning only**.

```text
memory.record(record_id pk, subject_id, kind text, key text, value jsonb, evidence_class in ('observed','derived','self_reported'),
              confidence real null, evidence_ids uuid[] not null check (cardinality(evidence_ids) >= 1),
              validator_version text, created_at, superseded_by null)
```

Allowlisted `kind`s (anything else is rejected):

| kind | key | value example |
|---|---|---|
| `capability` | kc_id | `{"state":"pass_unaided","assistance":0}` (mirror of latest transition) |
| `misconception_hypothesis` | kc_id:misconception_id | `{"label":"off_by_one_window_end","confidence":0.6,"alternatives":[...]}` |
| `representation_outcome` | representation_id | `{"next_check_unaided_rate":0.8,"n":5}` |
| `operation_outcome` | operation | `{"helped_rate":0.7,"n":6}` |
| `retention` | kc_id | `{"due_at":"...","stability":3.2}` |
| `pace_preference` | `session_length` / `examples_first` | `{"value":"short"}`; learning-mechanics only, from explicit settings |
| `goal` | subject | `{"exam":"HESI","target_date_bucket":"2026-Q4"}`; month/quarter granularity only |

Scope rules (enforced by the validator, P-MEM-1..5):
1. **Only these kinds.** No free-form "facts".
2. **Evidence-linked.** At least one event id per record. Derived records carry a confidence and alternatives where relevant.
3. **Off-scope filter.** Reject values that mention health/medical status of the learner, family/relationships, work schedule/employer, location, age, names, contact details, or emotions not attached to a learning event. (Nursing *content* is in scope; the learner's own health is not.)
4. **Self-report stays self-report.** It never sets `capability`.
5. **Rebuildable.** Memory is a projection. A nightly job rebuilds it from events, and a diff alerts on drift.
6. **Learner control.** Learners can view their memory as a rendered `learner.md` and delete records (`superseded_by` = tombstone). Events are kept.

`learner.md` (rendered, ≤400 tokens, for LLM context) contains: current KC states, top two active misconception hypotheses with confidence, representations/operations that helped, due reviews. It has no handle and no dates finer than a day.

## 5. Retention

- `learn.*`: kept indefinitely (evidence). Learner export: JSON of their subject's events.
- `ux.timing`: 180 days raw, then aggregated.
- `auth.session`: purged 30 days after expiry.
- Account deletion: `auth.account` and `auth.account_subject` are removed. Learning events stay pseudonymous under `subject_id`, or are purged if the learner requests full erasure (a documented exception to append-only, executed by an admin script with an audit row).
