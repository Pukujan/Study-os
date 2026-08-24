# Study OS

Study OS is a **research-first learning system** for observing, modeling, and improving how a learner translates technical concepts between representations.

The first vertical slice is **DSA in Python**, with `subject-001` as the initial longitudinal design participant.

> Current status: **Research Gate R0 — research harness readying.** Broad product/UI work is deliberately gated until one complete learning trajectory demonstrates immediate improvement, scaffold fading, transfer, and delayed retention.

## Mission

Convert AI-assisted study sessions into auditable evidence about:

1. where understanding breaks;
2. which representation or learning operation was attempted;
3. what changed after the intervention;
4. whether improvement survives removal of assistance;
5. whether it transfers to a changed problem;
6. whether it persists after delay.

The target is not syntax memorization for its own sake. The target is **AI leverage with human technical control**: enough unaided reasoning to trace, explain, implement, test, debug, and adapt code even when AI is available.

## Core hypothesis

A learner may fail at a **representation transition** rather than at an entire concept.

For DSA, the relevant chain might be:

`problem -> recognition -> mental model -> state -> invariant -> semantic procedure -> pseudocode -> code -> debugging -> transfer`

Study OS records those transitions and can adapt across representations such as prose, figures, Mermaid flowcharts, deterministic state traces, invariants, pseudocode, code scaffolds, executable code, and later carefully validated audio/video.

The system must not treat “I understand” as mastery. Self-report, observed behavior, intervention history, transfer, and delayed retention remain separate evidence.

## Subject 001

The first design participant has a useful transition profile for this research question:

- prior coding experience centered on JavaScript;
- no completed formal Python learning sequence;
- extensive use of AI to build scripts and technical projects;
- can often make code work with AI assistance while wanting stronger unaided Python/DSA fluency;
- wants manual code comprehension, debugging, algorithmic reasoning, and implementation skill without rejecting AI assistance;
- can report live where an explanation fails and why a changed representation did or did not help;
- can participate in repeated and delayed assessments.

This makes Subject 001 a high-information **design participant** for studying the boundary between AI-assisted productivity and internalized procedural competence. It does **not** make one participant representative of learners generally.

## What the research currently supports

The project is built around several evidence-backed ideas, with important constraints:

- worked examples and explicit subgoals can help novices acquire procedural schemas;
- active prediction/explanation around program visualizations is more defensible than passive watching;
- retrieval practice and spacing matter for durable learning;
- carefully structured AI tutoring can help, but pedagogy should not live only in an LLM prompt;
- AI-assisted programming increases the importance of being able to inspect, reason about, debug, and correct generated code;
- N=1/single-case methods can be useful for repeated within-person experimentation, while population generalization remains a separate research stage;
- the project **does not** assume fixed visual/auditory learning styles;
- more modalities are not automatically better and can increase cognitive load.

See:

- [`docs/RESEARCH_FOUNDATIONS.md`](docs/RESEARCH_FOUNDATIONS.md)
- [`docs/SOURCE_INDEX.md`](docs/SOURCE_INDEX.md)
- [`docs/RESEARCH_STATUS.md`](docs/RESEARCH_STATUS.md)
- [`docs/RESEARCH_QUESTIONS.md`](docs/RESEARCH_QUESTIONS.md)
- [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md)

## Atomic unit

The atomic unit is a **learning episode**:

`learner state -> task -> attempt -> failure/uncertainty -> diagnosis hypothesis -> intervention -> re-attempt -> assessment -> fade -> transfer -> delayed evidence`

A chat session can contain many learning episodes. A lesson can span many sessions.

## Evidence model

Keep three evidence classes separate:

1. **Observed** — what happened: answer, score, hint count, transcript span, elapsed time.
2. **Self-reported** — what the learner says was confusing/helpful and why.
3. **Derived** — model/system interpretations such as “likely invariant-to-control-flow translation failure.”

Derived labels are hypotheses, not ground truth.

See [`docs/MEASUREMENT_MODEL.md`](docs/MEASUREMENT_MODEL.md).

## Research Gate R0

Before expanding into a broad DSA product, rich multimodal generation, or production UI, Study OS must produce one complete auditable Sliding Window trajectory with:

- private raw evidence preserved and hashed;
- provenance-aware transcript normalization;
- a failure transition identified;
- a versioned representation + learning operation;
- immediate behavioral assessment;
- assistance removal/fading;
- changed-surface transfer;
- delayed retrieval;
- comparison of self-report and behavior;
- enough repo state for a new agent to reconstruct the experiment.

See [`docs/BUILD_GATES.md`](docs/BUILD_GATES.md) and [`docs/RESEARCH_PLAN.md`](docs/RESEARCH_PLAN.md).

## Project boundary

Study OS owns:

- raw learning-session evidence and immutable transcript captures;
- learning events and episodes;
- learner-state snapshots;
- representation definitions and versions;
- lesson intermediate representations;
- assessment, retention, and transfer evidence;
- experimental comparison of learning interventions.

Study OS does **not** initially own:

- a general-purpose knowledge graph platform;
- general RAG infrastructure;
- universal claims about how all humans learn;
- a full DSA curriculum;
- production multimodal generation infrastructure.

See [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md), [`docs/PROJECT_BOUNDARY.md`](docs/PROJECT_BOUNDARY.md), and [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md).

## FOSSIL boundary

Study OS uses a dedicated learning schema. FOSSIL is a good fit for durable provenance, promoted research knowledge, lesson hypotheses, curated learning trajectories, and long-lived knowledge packs, but it should not be required for every learning micro-event.

Canonical flow:

`raw transcript -> Study OS events/episodes -> learner/lesson state -> optional FOSSIL export`

See [`docs/FOSSIL_INTEGRATION.md`](docs/FOSSIL_INTEGRATION.md).

## Transcript ingestion

A deterministic first-stage utility exists at `tools/ingest_transcript.py`. It preserves source bytes, refuses to overwrite immutable raw evidence, hashes artifacts, and creates the session manifest.

The intended assistant surface is described by [`plugins/study-os-ingest/skill.md`](plugins/study-os-ingest/skill.md):

`@study-os-ingest ingest this learning session`

The skill contract exists in the repo, but the @-mentionable plugin/skill is **not yet packaged/registered** in ChatGPT.

Because this repository is public, full raw transcripts are local/private by default and excluded by `.gitignore`.

## Agent-maintained project state

Agents should be able to continue the project without relying on hidden chat context.

- [`AGENTS.md`](AGENTS.md) — stable operating/integrity rules.
- [`PROJECT_MANIFEST.yaml`](PROJECT_MANIFEST.yaml) — machine-readable current scope, gates, schema versions, privacy/FOSSIL policy, and risks.
- [`docs/HANDOFF.md`](docs/HANDOFF.md) — current operational snapshot.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — durable boundary/research decisions.
- [`docs/AGENT_RESEARCH_PROTOCOL.md`](docs/AGENT_RESEARCH_PROTOCOL.md) — how agents update the research harness while the learner focuses on learning.

“Self-updating” means agents are required to update these explicit state artifacts when their work changes project state; it does not mean the repository runs asynchronous autonomous work by itself.

## CI/CD

Continuous integration is appropriate now because data/provenance corruption can invalidate learning evidence just as code regressions can invalidate software.

Current CI checks:

- Python compilation;
- schema validity;
- committed session-data validity;
- project-manifest invariants;
- accidental public tracking of private raw transcripts;
- deterministic transcript-ingest unit tests.

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

Continuous deployment is intentionally deferred until Research Gate R0 and a stable application surface exist.

See [`docs/CI_CD.md`](docs/CI_CD.md).

## Repository layout

- `docs/` — charter, research, failure modes, methodology, gates, decisions, handoff.
- `schemas/` — versioned canonical Study OS data contracts.
- `domains/` — domain/concept/lesson knowledge and representations.
- `sessions/` — public-safe manifests/derived session records; raw evidence stays private by default.
- `subjects/` — learner-model snapshots and subject-specific state.
- `datasets/` — curated golden trajectories, transfer sets, and retention sets.
- `plugins/` — assistant/agent skill contracts, beginning with transcript ingestion.
- `tools/` — deterministic ingest and repository validation utilities.
- `tests/` — deterministic tests.
- `fossil/` — optional generated/exported FOSSIL-compatible artifacts; never the Study OS source of truth.

## Current next milestone

Verify CI, define the deterministic Sliding Window lesson/state model and matched evaluation items, then run **one complete instrumented learning trajectory** for Subject 001.

The evidence from that trajectory—not the availability of more AI modalities—decides what gets built next.
