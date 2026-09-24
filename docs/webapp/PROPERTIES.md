# Property-driven specs, and success/fail conditions

Each property is stated so that a test can check it. The suggested test style is `hypothesis`, which is available for dev use only and would need to be added to the dev lock in the implementing task; `unittest` is the current baseline. IDs are stable so that tests, detectors, and dashboards can cite them.

Notation: **P-xxx** = invariant (must always hold; a violation is a bug). **Test** = how to check it.

## 1. System-wide invariants

| ID | Property | Test |
|---|---|---|
| P-SYS-1 | **No personal data is persisted.** No table column outside `auth.account.handle` holds a user-chosen identifier, and no persisted text contains an email, phone number, street address, IP address, or user agent. | Schema allowlist test (column names/types vs `docs/webapp/DATA_MODEL.md`). Hypothesis: generated PII strings sent in attempts/reactions never appear in any row (full-DB scan after the test run). |
| P-SYS-2 | **Learning data is pseudonymous.** No `learn.*`, `ux.*`, or `memory.*` table references `auth.account` directly. Only `subject_id` is used. | Schema FK graph test. |
| P-SYS-3 | **Evidence is append-only.** UPDATE and DELETE on `learn.*` and `ux.*` event tables fail. | DB test issuing UPDATE/DELETE as the app role → permission error, and the trigger raises. |
| P-SYS-4 | **Determinism.** The same `(controller state, event, module_version_set)` produces the same `(state', effects)`. | Hypothesis: random event sequences are replayed twice → identical transition logs. |
| P-SYS-5 | **No silent learner-evidence loss.** Every accepted attempt (HTTP 2xx) has exactly one `learn.attempt` row. Idempotent replays create none. | Property test with random retries/duplicates of idempotency keys. |
| P-SYS-6 | **Versioned modules.** Every turn records `controller_revision`, `pir_revision`/`pack_revision`, `interpreter_route`, `prompt_template_version`, and `validator_version` when applicable. | Row-level NOT NULL + test that joins every turn to a module version set. |
| P-SYS-7 | **Private repositories are never ingested.** No build or runtime path reads from `Pukujan/private-study-log`. | CI grep/guard on config + dependency manifest. |

## 2. Component properties

### 2.1 Controller (#90)

| ID | Property |
|---|---|
| P-CTL-1 | **Answer never revealed before an attempt.** For every probe step, no learner-visible payload (turn markdown, chart spec, API JSON) emitted before the first attempt contains the hidden answer or a forbidden component. |
| P-CTL-2 | **Mastery never claimed without evidence.** No state or learner-visible text says "mastered"/"you've mastered"/"complete mastery" unless the KC has `pass_unaided` ∧ `pass_transfer` ∧ `pass_delayed` ∧ ≥2 unseen items correct at A0. Even then, the wording comes from a fixed template. |
| P-CTL-3 | **Error path.** `incorrect` → correction on the same chart → retry with a **different** example (different item id and different numeric instance) → on correct, one more different check before `ADVANCE`. |
| P-CTL-4 | **Partial path.** `partial` keeps the recognized part and isolates the missing sub-step, and does not advance. |
| P-CTL-5 | **One relation, one picture, one question** per presented step. The asset declares `new_relations == 1` and the rendered turn contains exactly one question. |
| P-CTL-6 | **Persistent chart.** When a step declares `required_components` (e.g. array, index row, box, `k`), every turn for that step, including LLM rewrites, contains them. |
| P-CTL-7 | **Help fades.** After two consecutive correct answers at level A*n*, the next step's assistance ceiling is ≤ A*n−1* until A0 (or until the step's floor). |
| P-CTL-8 | **Assistance ceiling respected.** No turn exceeds the step's assistance ceiling. An A6 (full solution) turn is only emitted after the policy's explicit give-up rule, and it marks the KC `pass_supported` at most. |
| P-CTL-9 | **Progression is code-owned.** The LLM output schema has no field that can change `current_step_id`, capability state, or schedule. Model-based test: an LLM stub returning arbitrary JSON cannot change the transition sequence beyond `grade` outcomes, and grade outcomes need confidence ≥ 0.7. |
| P-CTL-10 | **Self-report is not evidence of mastery.** "I get it" / reaction 👍 never changes a capability state. |
| P-CTL-11 | **Terminal honesty.** The DSA lesson exit is `ASSEMBLED_MASTERY_UNPROVEN` (as in SOS-0002). Session summaries list capability states and the next review date only. |

### 2.2 Graders (#90, #91)

| ID | Property |
|---|---|
| P-GRD-1 | Deterministic graders are total: every input maps to exactly one of `correct/partial/incorrect/unresolved` without raising. |
| P-GRD-2 | Grading is invariant to whitespace and case, and to option order for SATA. Dosage grading uses unit-aware tolerance, and unit conversions round-trip. |
| P-GRD-3 | Holdout/transfer items are never in tutor-visible content or in LLM prompts before their use. |

### 2.3 API and auth (#85, #86)

| ID | Property |
|---|---|
| P-API-1 | No endpoint response contains `expected_values`/`expected_text`/`correct_option` for an unattempted probe. |
| P-API-2 | Cross-account isolation: for random pairs (A, B), A's session cannot read or write B's sessions, memory, or progress (403/404). |
| P-API-3 | State-changing endpoints reject a missing/foreign `Origin` or a missing `X-Study-OS` header. |
| P-API-4 | Passphrases are stored only as argon2id hashes. Login timing for an unknown handle ≈ a known handle (dummy hash). |
| P-API-5 | Logs contain no attempt free-text, passphrases, cookies, or API keys (log-capture test with canary strings). |

### 2.4 LLM interpreter and validator (#89)

| ID | Property |
|---|---|
| P-LLM-1 | **LLM output always passes controller validation before it is learner-visible or state-affecting.** Invalid output → one repair attempt with the violation codes → otherwise the canonical deterministic content is served and `INTERPRETER_FALLBACK` is recorded. |
| P-LLM-2 | The validator rejects: the hidden answer (token-boundary match, including spelled numbers), forbidden components, mastery language, more than one `?`, `new_relations ≠ 1`, missing required chart components, more words than the step budget, PII patterns, and links/URLs. |
| P-LLM-3 | Prompts never contain account ids, handles, or session cookies. They contain only PII-scrubbed current-attempt text and step content. |
| P-LLM-4 | Every call records route, model, snapshot id, tokens, cost, latency, and validation result. No prompt text goes into telemetry. |
| P-LLM-5 | Spend guard: when month-to-date cost ≥ the cap, interpreter operations degrade to deterministic fallbacks and learning continues. |
| P-LLM-6 | A route change is a new `interpreter_route` module version (recorded, never silent). |

### 2.5 Memory (#88)

| ID | Property |
|---|---|
| P-MEM-1 | Only allowlisted kinds are stored (DATA_MODEL §4). Any other kind is rejected. |
| P-MEM-2 | Every memory record cites ≥1 existing `learn.turn`/`learn.attempt` id, carries an evidence class, and derived records carry a confidence. |
| P-MEM-3 | Off-scope content is rejected (health, family, location, work schedule, emotions not tied to a learning event, names). Tested with adversarial generated proposals. |
| P-MEM-4 | Self-report never produces a capability claim. |
| P-MEM-5 | Deleting memory never deletes learning events. Memory can be rebuilt from events (projection determinism). |

### 2.6 Frontend (#84)

| ID | Property |
|---|---|
| P-FE-1 | The client bundle and network payloads contain no answer data for an unattempted probe (payload inspection in e2e). |
| P-FE-2 | Charts are rendered only from API chart specs (no client-side invention). A snapshot test runs per chart spec. |
| P-FE-3 | Works under `/study-os/*` via the rewrite (deep link + refresh + assets). |
| P-FE-4 | No third-party network requests (e2e request interception allowlist). |

## 3. Session success and fail conditions

A **session** runs from `START` to `SESSION_DONE`/`PAUSED`/`BLOCKED`.

**Session success (all must hold):**
1. At least one learner attempt is recorded, and every due review item was offered before new material (or none were due).
2. No invariant violation occurred (P-CTL-*, P-LLM-1/2, P-SYS-1).
3. Every incorrect answer was followed by the error path (P-CTL-3), and the session did not end in the middle of a correction.
4. The summary shows capability-state changes that are backed by evidence ids.

**Session soft-fail (a UX signal, not a bug):** the learner abandons within 2 min of a correction; ≥2 "frustrated" reactions; ≥3 consecutive incorrect answers on one step; an interpreter fallback rate > 30% in the session. These feed the friction dashboard and the promotion/rewrite queue.

**Session hard-fail (a bug; alert):** any P-* violation reaches the learner or the DB; lost attempt; a controller exception that leaves no resumable state; `BLOCKED` without a recorded reason.

## 4. Product success and fail conditions

Measured per learner (N=1 each; within-learner product evidence only, not population claims).

**Success after 4 weeks of beta:**
- Engagement: each learner completes ≥4 sessions/week in ≥3 of 4 weeks.
- Learning signal: ≥60% of KCs that reached `pass_unaided` also reach `pass_delayed` at their first scheduled delayed check. For HESI: the delayed-review correct rate trends up over weeks.
- Help efficiency: median assistance level at first correct answer falls over repeated KCs.
- UX: the share of steps with a "frustrated" reaction trends down, and the "helped" share of corrections is ≥50%.
- Tutor quality: 0 learner-visible invariant violations. Interpreter first-pass validation rate ≥95%. T1 agent-eval pass ≥98% of turns.
- Operations: API availability ≥99% (home host, measured), p95 deterministic-turn latency <300 ms, p95 interpreter turn <10 s, 0 data loss (restore drill passes monthly).
- Cost: interpreter spend ≤ US$5/month at beta volume (a guard, not a goal; Alex prioritizes quality).

**Product fail / stop-and-fix triggers:** any answer leak or mastery claim in production; any personal data found in storage; a learner stops using it for 7+ days after reporting frustration (interview before building more); the promotion loop promotes a generation that fails the golden conformance tests.
