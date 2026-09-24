# Architecture

## 1. Principle

```text
precompiled lesson graph (PIR / subject pack)   ← authored + reviewed + promoted generations
            │  deterministic, no model call
            ▼
web session controller (pure state machine)  ── owns progression, assistance ceiling, fade, capability states;
            │                                     next step = rules + pyBKT + FSRS (bandit later)
            │ learner input
            ▼
interpretation cascade (typed; every decision logged)
   1. rules: MCQ key / exact / regex / integer / trace / unit tests            $0, ms
   2. hosted Jev (OpenRouter Decisions API, pinned typesafe/jev-1.13): grading (noul per rubric point / choice), misconception (choice + none_of_these)
                                                                               ≈$0, 70–500 ms
      Laya-421M on gravebuster: frustration / wants-answer / sentiment only (after calibration; never gates progression)
   3. frontier LLM via IRE (cb/glm-5.3 → cb/deepseek-v4.1-flash): only when confidence < τ, or to rewrite a failed step
            │ typed proposal
            ▼
controller validation  ── pass → effect applied / shown      fail → repair once → canonical fallback
            │
            ▼
append-only learning + UX + decision events (xAPI-shaped) → learner memory (derived) → analytics (Metabase; PostHog UX mirror)
            │
            └─► promotion: validated generations that helped → reviewed → new graph revision
                decisions a rule reproduces ≥98% → new state-machine rule (upgrade path c)
```

This is ADR-0016 applied to the web, with the decision layer adopted from [DEEP_RESEARCH.md](DEEP_RESEARCH.md) §6.7–6.8 and §7.5. **The hot path makes no model call.** A typed decision model runs only when rules cannot classify an input. A frontier LLM runs only when the decision model is below its confidence threshold, or when the controller authorizes `rewrite_failed_step`. Every accepted generation is a candidate asset. Once reviewed and promoted, it is served deterministically to later learners, which drives the marginal cost per learner toward zero.

## 2. Components

| Component | Tech | Responsibility | Issue |
|---|---|---|---|
| Web client | Vite + React + TS, React Router (`basename=/study-os`), TanStack Query, SVG chart components | Render turns and chart specs, collect attempts and reactions, no pedagogy logic | #84 |
| API | FastAPI + uvicorn, Pydantic strict models, SSE | Auth, session endpoints, idempotent attempt ingestion, streaming turns | #85 |
| Session controller | Pure Python (`study_os.web.controller`) wrapping `study_os.pir.controller` | State machine (§3), capability-state transitions, FSRS scheduling | #90 |
| Graders | Deterministic: integer/sequence/text (existing `classify_response`), MCQ/SATA/order/dosage (new) | Classify attempts. Emit `UNRESOLVED` when unsure, so the case goes to the interpreter | #90, #91 |
| Decision layer | Typed decision client with two transports behind one question spec: OpenRouter Decisions API (`https://openrouter.ai/api/alpha/decisions`, pinned `typesafe/jev-1.13`, `OPENROUTER_API_KEY`) and a Jev-compatible `/v1/systemone` (Laya via `laya-serve` on gravebuster; swappable via `jev-compatible-server`/`llm2jev`); per-type temperature and τ config | Typed decisions: grade, misconception, affect/intent; decision log; 5% audit sampling | #97 |
| LLM interpreter | InferHub OpenAI-compatible client, forced tool/JSON schema | Low-confidence escalation of `grade_free_text`/`diagnose_misconception`, `rewrite_failed_step`, `propose_memory` | #89 |
| Validator | Deterministic | Schema, answer-leak, mastery-language, one-question, one-relation, chart-preserved, word budget, PII | #89, #90 |
| Memory | Postgres `memory.*` + `learner.md` renderer | Evaluation-scoped learner model | #88 |
| Store | Postgres 16 | Append-only `learn.*`, `ux.*`; `auth.*`; `analytics.*` views | #87 |
| Analytics | Metabase OSS, DuckDB; PostHog Cloud (non-PII UX mirror) | Learning dashboards over `analytics.*`; UX funnels/flags/experiments | #93 |
| Evals | pytest harness + persona agents | Agent-vs-agent conformance | #92 |
| Edge | Vercel (static app), Cloudflare Tunnel (API) | Serving and exposure | #94 |

Code location: everything lives in this repository (`web/` for the client, `src/study_os/web/` for the server), so controller semantics and the web surface are versioned together. design-bakery only gains rewrite rules.

## 3. Web session state machine

```text
START ─► REVIEW_DUE ─(none due)─► PRESENT_STEP
            │ (due items)                 │
            ▼                             ▼
        PRESENT_STEP ◄──────────── ADVANCE ◄─ CHECK(pass)
            │ probe                        ▲
            ▼                              │
        AWAIT_ATTEMPT ─(timeout/leave)─► PAUSED (resumable)
            │ attempt
            ▼
        GRADE ─(unresolved)─► INTERPRET ─(invalid ×2)─► GRADE_AS_UNRESOLVED → FEEDBACK(neutral, ask again)
            │ correct / partial / incorrect
            ▼
        FEEDBACK
          correct   → "why" on the same chart → CHECK (optional confirm) → ADVANCE / FADE
          partial   → keep the correct part, isolate the missing step → AWAIT_ATTEMPT (same step)
          incorrect → correction on the chart + reassurance → RETRY_DIFFERENT (different example)
                        → AWAIT_ATTEMPT → correct → CHECK (one more different example) → ADVANCE
                        → incorrect again → rewrite_failed_step (interpreter, if authorized) or smaller_step
        wheel-spinning (≥10 opportunities on a KC without 3 correct in a row) → stop drilling → prerequisite probe
        repeated failure beyond the policy limit → BLOCKED (flag for review; never fake progress)
        end of plan → SESSION_DONE (summary: capability states + next review date; never "mastered")
```

Each transition is recorded as a `learn.turn` with `(state_before, event, state_after, controller_revision, module_version_set)`. For the DSA lesson, the PIR asset's own step graph is embedded in `PRESENT_STEP…ADVANCE`. The web controller adds the session-level states (review, pause, summary, capability promotion) and never overrides PIR transitions.

Capability promotion (per KC) follows the existing states. `pass_supported` means correct at A1–A6. `pass_unaided` means correct at A0. `pass_transfer` means an unaided correct answer on an unseen transfer item. `pass_delayed` means an unaided correct answer on a later day without re-teaching. "Mastery" is only ever a derived label requiring **unaided + transfer + delayed + 2 unseen items**, and the UI still words it as "strong evidence", not a guarantee.

## 4. Interpretation cascade

### 4.1 Tiers

| Decision | Tier 1: rules | Tier 2: decision model (Jev-compatible) | Tier 3: frontier LLM (IRE) | Stakes gate |
|---|---|---|---|---|
| Grade an attempt | MCQ/SATA key, integer/sequence, exact/regex text, dosage with units, trace equality, code unit tests | Hosted Jev via OpenRouter (`typesafe/jev-1.13`): `noul` per rubric point + `choice` {pass, partial, fail} | `grade_free_text` when Jev confidence < τ_grade, or a `none` label | Grades that feed `pass_unaided`/`pass_transfer`/`pass_delayed` need rules, **or** Jev ≥ τ_mastery (stricter), **or** LLM + Jev agreement. Otherwise record `unresolved` and ask again |
| Which misconception | Regex/trace patterns promoted from logs (path c) | Hosted Jev via OpenRouter `choice` over the node's misconception list + `none_of_these` | `diagnose_misconception` on low confidence or `none_of_these`; the output feeds new-misconception discovery | Stored as a `derived` hypothesis only |
| Frustration / wants the answer / sentiment | Behavioral rules (e.g. 3+ fails in a row ∧ latency rising ∧ help ≥ A3; rapid resubmits under 2 s) | **Laya-421M** on gravebuster (`choice`, not `noul`, per Laya issue #156), active only after calibration | none | Low stakes. May shorten a step or offer a break. **Never gates progression** |
| Rewrite a failed step | — | — | `rewrite_failed_step` (the only true generation duty) | Full validator (PROPERTIES §2.4); stored as a promotion candidate |
| Next step | Rules/state machine + pyBKT + FSRS | — | never | Deterministic; bandit later among equally valid actions, with propensity logged |

Thresholds τ are fitted per question type on a **Study OS public split** of reviewer-labelled decisions (target ≥95% precision in the auto-accept band). A blind split is kept untouched, following the eval-lab protocol. τ is re-fitted whenever a model version is pinned (e.g. `jev-1.13.0`, a `laya@<commit>`). Until enough labels exist, τ starts conservative (e.g. 0.9) and more decisions escalate to tier 3. That costs a little more, but it is safe.

**Day-one decision logging** (DATA_MODEL `learn.decision`): state hash, full question schema, model id and version, full probability distribution, confidence, threshold, route, escalation outcome, latency, cost, and later the ground truth (reviewer label, next unaided outcome, learner dispute). **About 5% of high-confidence tier-2 decisions are randomly also sent to tier 3 or to review** (`audit_sample=true`), so precision in the auto-accept band can be measured.

### 4.2 LLM operations (tier 3)

| Operation | When the controller calls it | Output (tool schema) | Validation |
|---|---|---|---|
| `grade_free_text` | Tier 1 cannot classify and tier 2 is below τ (or unavailable) | `{outcome: correct/partial/incorrect/unresolved, matched_expectations[], misconception_ids[], confidence}` | outcome ∈ enum; misconception ids ∈ the step's listed set; confidence < 0.7 ⇒ `unresolved` |
| `diagnose_misconception` | Tier 2 is low-confidence or returns `none_of_these` | `{hypotheses:[{id, confidence, evidence_turn_ids}]}` | ids ∈ the KC catalog, or `new_candidate` with a description (goes to review); stored as `derived` |
| `rewrite_failed_step` | Same step failed twice and the policy authorizes it | `{markdown, chart_spec_ref, question, new_relations:1, operation}` | full validator (PROPERTIES §2.4); the chart spec must equal the step's chart spec or an allowed variant |
| `propose_memory` | Session end | `{ops:[{op, kind, key, value, evidence_turn_ids}]}` | memory scope rules (DATA_MODEL §4) |

Envelope rules (all tiers that see learner text): send only step context and the PII-scrubbed current answer. Never send account ids, handles, or free-form personal notes. The hidden answer appears only as a "must not appear" constraint for rewrites. Streaming is on for tier 3, and tool/JSON output is forced.

### Promotion loop (cheap scaling)

1. An accepted `rewrite_failed_step` output is stored as `learn.generation` with its validation result.
2. Outcome linkage: did the learner answer the following check correctly, unaided?
3. Generations whose outcomes are positive across at least N distinct learner-sessions (N=2 while there are two learners; configurable) become `promotion_candidate`s.
4. Human review, or the owner approving in an admin view, turns a candidate into a new PIR asset revision (a new `canonical_pir_revision`). CI conformance tests run against the goldens (SOS-0002 evaluator).
5. The promoted variant becomes a deterministic alternative step served without an LLM call. Historical events keep their old revision (evidence immutability).

Replay of old trajectories against a new revision is counterfactual evaluation, never learner evidence (invariant 10 in HANDOFF).

## 5. Hosting topology

```text
learner browser
   │ https://www.design-bakery.com/study-os/...        (Vercel: design-bakery project)
   │     rewrite /study-os/:path* → https://study-os-web.vercel.app/study-os/:path*   (Vercel: study-os-web project)
   │
   │ fetch/SSE https://study-api.design-bakery.com/...  (Cloudflare proxied DNS → named tunnel)
   ▼
gravebuster (Ubuntu 24.04, Docker Compose, no inbound ports)
   ├─ cloudflared  (tunnel: study-api.design-bakery.com → http://api:8000)
   ├─ api          (FastAPI, uvicorn, 2 workers)
   ├─ postgres:16  (volume /srv/study-os/pg, nightly pg_dump → /srv/study-os/backups, 14 dailies + 8 weeklies)
   ├─ metabase     (bound to the tailscale interface only: http://gravebuster.tail733a0f.ts.net:3000)
   ├─ laya         (laya-serve, CPU/ONNX, internal network only, LAYA_API_KEY set; slice 2, after calibration)
   └─ secrets      (/srv/study-os/.env, mode 600: DB password, session secret, INFERHUB_API_KEY, OPENROUTER_API_KEY, LAYA_API_KEY, POSTHOG_PROJECT_KEY)
admin: ssh gravebuster over Tailscale (yoav)
```

design-bakery `vercel.json` addition (placed above the SPA catch-all, mirroring `/ai-for-good`):

```json
{ "source": "/study-os", "destination": "https://study-os-web.vercel.app/study-os/" },
{ "source": "/study-os/:path*", "destination": "https://study-os-web.vercel.app/study-os/:path*" }
```

The `study-os-web` project builds `web/` with Vite `base: '/study-os/'`. Its own `vercel.json` rewrites `/study-os/((?!assets/).*)` to `/study-os/index.html` for client routing. Assets therefore resolve at `/study-os/assets/*` on both hosts. This avoids the root-asset collision that `/ai-for-good` works around with extra per-folder rules.

Deploy: GitHub Actions builds and pushes an API image to GHCR on merge to `main` (after required CI). On gravebuster, a systemd timer (or Watchtower limited to the `api` container) pulls the signed tag and restarts. CI never needs inbound SSH, and no deploy credentials are exposed to PR code. Frontend: Vercel Git integration on the `study-os-web` project (root directory `web/`).

## 6. Auth design

- `POST /auth/redeem-invite {invite_code, handle, passphrase}` → creates an account. Invite codes are single-use, created by an admin CLI.
- `POST /auth/login {handle, passphrase}` → argon2id verify (with a constant-time dummy hash for unknown handles) → server-side session row → `Set-Cookie: sos_session=<random 256-bit>; HttpOnly; Secure; SameSite=Lax; Path=/`, host-only on `study-api.design-bakery.com`.
- The client uses `fetch(..., {credentials:'include'})`. The API sets CORS `Access-Control-Allow-Origin: https://www.design-bakery.com` with `Allow-Credentials: true`. State-changing requests require the header `X-Study-OS: 1` and an allowed `Origin`.
- Rate limiting: login 5/min per handle plus a global bucket, with lockout backoff. Sessions: 30-day sliding window, revocable.
- Phase 2: passkeys (WebAuthn) as the primary login; the passphrase becomes a fallback.
- Authorization: every learning query is scoped by `subject_id` resolved from the session. The `admin` role can read aggregates and review promotion candidates, but gets no raw free-text by default.
