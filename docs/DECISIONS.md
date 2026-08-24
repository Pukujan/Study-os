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

**Status:** accepted

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

**Status:** accepted

Study OS may plan broader technical-development tracks without treating them as simultaneous research programs or validated learning domains.

The active Research Gate R0 scope remains exactly:

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

**Why:** recent real interview evidence exposed technical problem framing and AI-systems diagnosis as a meaningful learner-development need, while the R0 research gate still requires scope discipline. Separating curriculum architecture from active research scope allows Study OS to preserve both.

**Specification:** see `docs/LEARNING_CONTROL_MODEL.md`.
