# Architecture

## 1. Principle

```text
precompiled lesson graph (PIR / subject pack)   ← authored + reviewed + promoted generations
            │  deterministic, no LLM
            ▼
web session controller (pure state machine)  ── owns progression, assistance ceiling, fade, capability states
            │ needs interpretation?  (free text / unmatched answer / step failed twice)
            ▼
LLM interpreter (IRE/InferHub)  ── returns a typed proposal only
            │
            ▼
controller validation  ── pass → effect applied / shown      fail → repair once → canonical fallback
            │
            ▼
append-only learning + UX events  → learner memory (derived) → analytics views
            │
            └─► promotion queue: validated generations that helped → reviewed → new graph revision
```

This is ADR-0016 applied to the web. **The hot path makes no LLM call.** An LLM is called only when the deterministic grader cannot classify an answer, or when the controller authorizes a `rewrite_failed_step` operation. Every accepted generation is a candidate asset. Once reviewed and promoted, it is served deterministically to later learners, which drives the marginal cost per learner toward zero.

## 2. Components

| Component | Tech | Responsibility | Issue |
|---|---|---|---|
| Web client | Vite + React + TS, React Router (`basename=/study-os`), TanStack Query, SVG chart components | Render turns and chart specs, collect attempts and reactions, no pedagogy logic | #84 |
| API | FastAPI + uvicorn, Pydantic strict models, SSE | Auth, session endpoints, idempotent attempt ingestion, streaming turns | #85 |
| Session controller | Pure Python (`study_os.web.controller`) wrapping `study_os.pir.controller` | State machine (§3), capability-state transitions, FSRS scheduling | #90 |
| Graders | Deterministic: integer/sequence/text (existing `classify_response`), MCQ/SATA/order/dosage (new) | Classify attempts. Emit `UNRESOLVED` when unsure, so the case goes to the interpreter | #90, #91 |
| Interpreter | InferHub OpenAI-compatible client, forced tool/JSON schema | `grade_free_text`, `diagnose_misconception`, `rewrite_failed_step`, `propose_memory` | #89 |
| Validator | Deterministic | Schema, answer-leak, mastery-language, one-question, one-relation, chart-preserved, word budget, PII | #89, #90 |
| Memory | Postgres `memory.*` + `learner.md` renderer | Evaluation-scoped learner model | #88 |
| Store | Postgres 16 | Append-only `learn.*`, `ux.*`; `auth.*`; `analytics.*` views | #87 |
| Analytics | Metabase OSS, DuckDB | Dashboards over `analytics.*` | #93 |
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
        repeated failure beyond the policy limit → BLOCKED (flag for review; never fake progress)
        end of plan → SESSION_DONE (summary: capability states + next review date; never "mastered")
```

Each transition is recorded as a `learn.turn` with `(state_before, event, state_after, controller_revision, module_version_set)`. For the DSA lesson, the PIR asset's own step graph is embedded in `PRESENT_STEP…ADVANCE`. The web controller adds the session-level states (review, pause, summary, capability promotion) and never overrides PIR transitions.

Capability promotion (per KC) follows the existing states. `pass_supported` means correct at A1–A6. `pass_unaided` means correct at A0. `pass_transfer` means an unaided correct answer on an unseen transfer item. `pass_delayed` means an unaided correct answer on a later day without re-teaching. "Mastery" is only ever a derived label requiring **unaided + transfer + delayed + 2 unseen items**, and the UI still words it as "strong evidence", not a guarantee.

## 4. LLM interpreter operations

| Operation | When the controller calls it | Output (tool schema) | Validation |
|---|---|---|---|
| `grade_free_text` | Deterministic grader returns `UNRESOLVED` on a text step | `{outcome: correct/partial/incorrect/unresolved, matched_expectations[], misconception_ids[], confidence}` | outcome ∈ enum; misconception ids ∈ the step's listed set; confidence < 0.7 ⇒ treated as `unresolved` |
| `diagnose_misconception` | Two or more incorrect answers on a KC | `{hypotheses:[{id, confidence, evidence_turn_ids}]}` | ids ∈ the KC misconception catalog; stored as `derived` |
| `rewrite_failed_step` | Same step failed twice and the policy authorizes it | `{markdown, chart_spec_ref, question, new_relations:1, operation}` | full validator (PROPERTIES §2.4); the chart spec must equal the step's chart spec or an allowed variant |
| `propose_memory` | Session end | `{ops:[{op, kind, key, value, evidence_turn_ids}]}` | memory scope rules (DATA_MODEL §4) |

Envelope rules: the prompt contains the step's canonical content, allowed components, forbidden components, and the hidden answer **only as a "must not appear" constraint**. It never contains account ids, handles, or free-text beyond the current attempt (PII-scrubbed). Streaming is on (SSE to the client for rewrites). Tool/JSON output is forced.

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
   └─ secrets      (/srv/study-os/.env, mode 600: DB password, session secret, INFERHUB_API_KEY)
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
