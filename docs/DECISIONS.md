# Decision Log

This file records decisions that change project invariants, boundaries, or research interpretation. Routine implementation history belongs in Git/issues.

## D001 — Dedicated Study OS learning schema

**Status:** accepted

Study OS owns canonical session, event, episode, representation, lesson, assessment, and learner-state data.

FOSSIL remains an optional export/promotion target for durable claims, curated trajectories, research conclusions, and validated domain knowledge.

**Why:** learning sessions generate high-frequency process telemetry and subject-specific observations whose semantics are different from general-purpose durable knowledge claims. Forcing every micro-event through FOSSIL would couple the experiment to infrastructure that is not required to test the learning hypothesis.

**Revisit when:** Study OS has repeated trajectories and a concrete need for cross-domain durable knowledge queries.

## D002 — Raw transcripts private by default

**Status:** accepted

Full raw transcripts are not committed to the public Study OS repository by default. Public records contain hashes, redacted fixtures, manifests, schemas, and reviewed derivatives.

**Why:** transcript evidence may contain private or unrelated conversation content, and Git history is difficult to erase reliably once published.

## D003 — Subject 001 is a design participant, not a population proxy

**Status:** accepted

Optimize the first procedure for Subject 001 while preserving explicit evidence scope.

Promotion path:

`subject observation -> repeated subject finding -> lesson hypothesis -> replicated cross-subject finding`

No agent may skip these evidence scopes silently.

## D004 — No fixed learning-style classification

**Status:** accepted

Study OS may test visual, textual, auditory, formal, structural, and procedural representations. It will not infer or store a fixed “visual learner,” “auditory learner,” or similar sensory type as a causal learning rule.

**Why:** the common learning-styles matching hypothesis lacks adequate empirical support. Study OS instead selects representations from observed task/state/outcome evidence.

## D005 — Representation + operation are separate variables

**Status:** accepted

Examples:

- representation: deterministic state trace
- operation: predict

or

- representation: pseudocode
- operation: reconstruct

**Why:** “showing a diagram” and “asking the learner to predict from a diagram” are different interventions. Visualization research suggests active engagement matters.

## D006 — Deterministic algorithm state is authoritative

**Status:** accepted

Generated images/video may later illustrate a concept, but canonical DSA state transitions must come from a deterministic, testable state model/reference implementation.

**Why:** an attractive but incorrect pointer movement or queue state is a learning-data corruption event, not merely a UI bug.

## D007 — CI now; CD deferred

**Status:** accepted, clarified by D011

CI validates schemas, Python utilities, unit tests, data-boundary rules, and repository invariants on pushes/PRs.

Continuous deployment is deferred until Research Gate R0 produces one complete auditable learning trajectory and a product surface is actually justified.

## D008 — Build is gated by learning evidence

**Status:** accepted; sequencing partially superseded by D014

Before broad UI/multimodal expansion, R0 requires:

- preserved/hashable raw evidence;
- provenance-aware normalization;
- diagnosed failure hypothesis;
- versioned intervention;
- immediate behavioral assessment;
- assistance fading;
- transfer assessment;
- delayed retrieval;
- comparison of self-report and behavior;
- agent-reconstructable experiment history.

D014 later removes this as a global blocker on structured curriculum acquisition and ongoing product dogfooding. The evidence-quality requirements remain applicable to claims about intervention effectiveness.

## D009 — Agent state is explicit and reviewable

**Status:** accepted

Agents use root `AGENTS.md`, `PROJECT_MANIFEST.yaml`, and `docs/HANDOFF.md`.

Agents may update project state but may not silently relax invariants. Changes to boundaries/gates require this decision log or a future ADR.

## D010 — Local runtime owns live learner state

**Status:** accepted

Study OS v0.1 is local-first. The canonical operational learner state will live in a local Study OS runtime (initially WSL) backed by SQLite plus a private evidence store.

GitHub remains the source for code, schemas/migrations, research, issue logs, plugin/app definitions, tests, Lesson IR, and curated/redacted artifacts. GitHub is not the operational learner database.

The existing repository checkpoint files are bootstrap/research artifacts. Once the local runtime exists, canonical live checkpoints and current learner state belong in the local database; GitHub checkpoint snapshots become optional curated/reproducibility exports.

**Why:** high-frequency attempts, representation switches, scores, checkpoints, and private transcripts require structured low-latency storage and should not create commits or expose private data.

**Architecture:** see `docs/LOCAL_RUNTIME_ARCHITECTURE.md` and Issue #4.

## D011 — GitHub Actions is repository CI, never runtime infrastructure

**Status:** accepted

Study sessions, event recording, scoring, checkpointing, and resume must not depend on GitHub Actions.

Repository CI may remain useful for schemas, migrations, tests, app/plugin contracts, and public-data/privacy rules, but the local Study OS runtime must enforce its own startup/write-time invariants and provide a health/doctor check.

If Actions becomes distracting during R0, it may be reduced or disabled without changing Study OS runtime semantics.

## D012 — One semantic `@StudyOS` app surface

**Status:** accepted

The intended ChatGPT-facing integration is one `@StudyOS` app/plugin surface backed by semantic MCP tools such as `resume`, `record_attempt`, `record_assessment`, `record_representation_outcome`, `checkpoint`, and `status`.

Do not expose arbitrary SQL, shell execution, or unrestricted file mutation to the conversational model.

ChatGPT cannot directly reach a WSL-only `localhost` service. Integration must use a supported secure/private MCP tunnel or another deliberately secured remote path. The exact write-action capability is plan/workspace dependent and must be verified at integration time.

**Why:** the tutor should decide how to teach while Study OS owns deterministic persistence, provenance, scoring, checkpointing, and validation.

## D013 — Separate active research scope from planned competency tracks

**Status:** accepted; execution-scope restriction partially superseded by D014

Study OS may plan broader technical-development tracks without treating them as simultaneous research programs or validated learning domains.

The original active Research Gate R0 scope was exactly:

- Subject 001;
- DSA;
- Python;
- Sliding Window.

The planned curriculum architecture contains five competency tracks:

1. algorithmic foundations;
2. software and systems foundations;
3. system design and reliability;
4. AI systems, evaluation, and reliability;
5. technical problem framing and diagnosis.

The canonical conceptual control loop is:

`goal -> plan -> task/episode -> attempt -> test/assessment -> evidence -> capability state -> diagnosis/next action -> plan update -> transfer/delayed test`

Study OS currently has strong assessment/evidence/capability-state machinery, a partial planning mechanism, and only implicit goal representation. Do not add goal/plan schemas merely for completeness; add first-class runtime objects when the live learning loop requires durable multi-goal planning.

Scoring remains multidimensional and evidence-backed. Planned open-ended diagnosis exercises must score observable problem-framing behavior rather than whether the learner guessed a hidden root cause immediately.

**Why:** recent real interview evidence exposed technical problem framing and AI-systems diagnosis as a meaningful learner-development need, while the R0 research gate still required scope discipline. D014 later allows structured curriculum acquisition and operational dogfooding to expand in parallel without retroactively upgrading evidence claims from the original R0 work.

**Specification:** see `docs/LEARNING_CONTROL_MODEL.md`.

## D014 — Operational learning and durable data are the primary product-development loop

**Status:** accepted

Study OS will now prioritize real learner use, durable longitudinal evidence, and structured curriculum acquisition as parallel workstreams.

The current learner-facing surface remains the GPT app. A dedicated frontend is deferred, not rejected.

### Core product loop

```text
structured source material
 -> learner attempt
 -> observed/self-reported friction
 -> diagnosis hypothesis
 -> representation / information / assistance / granularity operation
 -> learner response
 -> fade / restore source difficulty
 -> transfer / retention when warranted
 -> learner + system evidence
```

### Durable-data invariant

> No silent learner-evidence loss.

A learner interaction must be either durably acknowledged by the local Study OS runtime or explicitly known to be missing/uncertain and recoverable through reconciliation/backfill.

The local runtime cannot guarantee capture of a remote turn that never reaches it. Therefore the end-to-end design must combine reliable local persistence with reconciliation of missing/unknown remote writes.

Preserve at least:

```text
raw/private evidence
 -> normalized operational records
 -> derived learner/system state
```

Derived state must retain provenance to lower-level evidence.

### Curriculum consequence

Approved public/open sources may be used to build structured curriculum in parallel with dogfooding. Curriculum expansion is no longer globally blocked on completing one narrow Sliding Window trajectory.

This does not weaken evidence standards for claims that a particular representation/intervention caused learning improvement.

### Representation consequence

Representation is a first-class adaptive product variable. Current subject-level operational hypotheses include:

- representation translation overhead;
- variable-name semantic interference;
- information overload/under-information;
- over-help/under-help;
- dynamic decomposition/recomposition;
- transformation fidelity and restoration to original/source representation.

These are contextual intervention/failure hypotheses, not fixed learner traits.

### Learner/system evaluation consequence

Learner capability and Study OS intervention quality must be evaluated separately. Immediate assisted correctness is not sufficient evidence for durable learner capability or system effectiveness.

### Architecture vs implementation consequence

The durable project assets are architecture, data semantics, provenance, contracts, curriculum structure, intervention semantics, invariants, and recovery guarantees.

Implementation code is replaceable. Engineering verification should be applied where it protects these durable assets or a concrete current product failure mode. Broad mutation programs, exhaustive hidden engineering holdouts, large synthetic learner simulations, chaos matrices, formal methods, and frontend/platform hardening are not blanket near-term roadmap gates unless a specific risk justifies them.

### Sequencing supersession

This decision partially supersedes the sequencing assumptions in D008 and D013:

- the narrow R0 evidence gate no longer blocks structured curriculum acquisition;
- Subject 001 may continue real course learning beyond the original Sliding Window-only experiment scope;
- product dogfooding and learning research run together rather than research having to finish before product use;
- historical R0 evidence remains scoped to the conditions under which it was collected and is not retroactively generalized.

### Frontend/multimodal consequence

Frontend, Mermaid/diagram rendering, audio tutoring, imagery, and later video remain valuable future representation surfaces. They should consume the same backend learning semantics and be activated when the owner promotes them in priority. They are not the present critical path while GPT dogfooding is coherent and productive.

**Roadmap:** see `docs/ROADMAP.md`.

## D015 — Study OS owns its continuity state; PCM and CGM are pinned helpers

Status: proposed in #78 (task `SOS-0001`); accepted when its PR merges.

This repository is the authoritative owner of Study OS project facts, continuity/task state, and human-facing claims. `Pukujan/project-continuity-modules` is adopted through its mature-repository overlay: `docs/PROJECT_CHARTER.md` is canonical PROJECT, `docs/HANDOFF.md` is canonical CURRENT, `tasks/` holds issue-backed PCM task projections, and `schemas/v1/` is an exact copy of the pinned protocol schemas. `Pukujan/content-generation-modules` is adopted as a pinned `.content-system/` adapter. Neither helper owns Study OS state, and neither is read from a moving branch during work.

No project invariant is relaxed. The existing documents keep their meaning; the `continuity:*` markers only declare roles. Pins, rules, and validation commands are in `AGENTS.md` → "Helper modules and project ownership".

## D016 — The shipped sliding-window lesson follows the two goldens step by step

Status: proposed in #80 (task `SOS-0002`); accepted when its PR merges.

The canonical sliding-window PIR asset (`sliding-window.max-sum-k.sep4.v1`) is generated from the two goldens in `domains/dsa/sliding-window/golden/`, and its scope stops where they stop (`enumerate(a)` and `append`). It moves to revision `sep4.sliding-window.golden-box-index-enumerate-append.v2`. Runs pinned to v1 fail closed on the existing revision check. `domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json` and `src/study_os/pir/conformance.py` mirror the `Pukujan/study-os-benchmarker` rules at `d438988` and are enforced by `tests/test_pir_golden_conformance.py`. Loop assembly, `max`, the `else` bridge, the stop condition, and `range(k)` need their own reviewed golden before they ship.

## D017 — Owner promotes a private hosted web app track (accepted, amended by D018)

Status: **accepted** on 2026-09-24 by Alex's assistant acting on his behalf (recorded in SOS-0004, #99), and amended the same day by D018. Proposed in #83 (task `SOS-0003`, epic #82).

Context: D014 says frontend surfaces start "when the owner promotes them". On 2026-09-24 Alex asked for a hosted web app (React at `design-bakery.com/study-os`, backend and database on his machine `gravebuster`, authenticated accounts for two real learners, LLM tutoring via IRE/InferHub).

Proposed decision:

- Promote a **private, invite-only web beta** for at most two learners, plus later invited beta users only after the invariants in `docs/webapp/PROPERTIES.md` have held for 4+ weeks.
- This narrowly relaxes the `AGENTS.md` deferral of production UI, CD/deployment, and production auth, **for this beta only**.
- No evidence invariant is relaxed. ADR-0016 still holds: lessons are precompiled step graphs served deterministically, and the LLM is an interpreter whose outputs pass controller validation. Synthetic agent-vs-agent results remain system evaluation, never learner evidence. No personal data is stored. Subject-level findings stay subject-level.
- The second learner's non-DSA subject (HESI) is added through subject packs that reuse the same capability, assistance, transfer, and retention semantics.

Spec: `docs/webapp/README.md`.


## D018 — Owner amendment to D017: self-hosted on gravebuster, open signup with Google, first-party analytics

Status: **accepted** by Alex (owner) on 2026-09-24, relayed by his assistant; recorded in SOS-0004 (#99). Detail: `docs/webapp/D018_AMENDMENT.md`.

Decision:

- **No Vercel.** Everything runs on `gravebuster`: the built React frontend is served by the API stack at `https://study.design-bakery.com/` and the API at `/api` on the same origin (first-party cookies), with Postgres 16, exposed through a Cloudflare named tunnel. The tunnel, ingress, and DNS are created through the Cloudflare API with Alex's tokens (no interactive login). R2 is optional (Postgres dump backups).
- **No PostHog.** All UX and learning events go to Postgres only, through a first-party tracker (`POST /api/events`) and Metabase-ready SQL views. Session replay (rrweb) is a separate later issue (#98).
- **Auth: open signup.** Google sign-in is primary (OIDC code flow with state + PKCE + nonce); a local email/passphrase fallback (argon2id) serves dev and use before Google keys exist. Minimal profile data is stored in `auth.*` only: Google subject, email, display name, learner handle. This **narrows P-SYS-1** for `auth.*` only: learning tables (`learn.*`, `ux.*`) still reference only the pseudonymous `subject_id`, free text is scrubbed, and no IP or user agent is stored (throttling uses an HMAC of the IP, purged after a day).
- Security baseline: server-side sessions in Postgres, HttpOnly Secure SameSite=Lax cookie, 30-day absolute and 7-day idle expiry, CSRF token on mutations, login throttling (5 failures / 15 min per account, 20 per IP, exponential backoff), per-IP and per-user rate limits, per-user daily model-call caps and a global daily spend cap.
- Caching: compiled lesson graphs in process memory; decision-model and LLM responses cached in Postgres by a hash of (model, prompt template, input); hashed static assets immutable behind the Cloudflare cache.
- **HESI:** the second learner (Alex's wife) consents and is the target learner. The HESI track becomes a checkpointed, topic-based program: a topic graph with prerequisites and section checkpoints mapped from the public HESI A2 sections (math, reading, vocabulary, grammar, anatomy and physiology, biology, chemistry) with HESI Exit content areas scaffolded. Topics are compiled into PIR teaching assets and served by the same deterministic controller as the sliding-window lesson. Content is original and cites openly licensed sources (OpenStax, Open RN, CDC); no commercial prep questions are copied. Every item carries an LLM review pass and stays `unreviewed` until Alex reviews it.

Unchanged: ADR-0016 deterministic control, the evidence invariants, and "synthetic evaluation is never learner evidence".

## D019 proposal - learner step review as append-only self-report

Status: proposed for issue #126 by A8 on 2026-09-25; implementation/acceptance belongs to InferHub A8-exec and the issue/PR record.

The learner player step review uses an intentional Submit of a 1-5 usefulness rating and nonblank typed why. The committed `ux.feedback` row is the review decision record, with step/variant/presentation context and an idempotency key. Exact retries return one receipt; a distinct review intent appends a new row. A re-render preserves step identity. Historical thumbs remain historical and decomposer review is a separate surface. Numeric opinion and rationale are self-report, never mastery evidence or `learn.*` review events. See `docs/webapp/SOS-0016_STEP_REVIEW_PDD.md`, `SOS-0016_STEP_REVIEW_SDD.md`, and `SOS-0016_STEP_REVIEW_TDD.md` for rationale, boundaries, and tests. Research Gate R0 and FOSSIL policy are unchanged.
