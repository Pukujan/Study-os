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

**Status:** accepted

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
