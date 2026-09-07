# Study OS Roadmap

Date: 2026-09-07
Status: canonical execution roadmap
Primary product tracker: #63
Known-PIR integration tracker: #66

## Product direction

Study OS is a deterministic learning-control layer between course/source material and a longitudinal learner record.

The core product problem is the learner ↔ course representation mismatch. AI may adapt decomposition, terminology, examples, traces, and representations, while deterministic code/state owns prerequisite satisfaction, progression, assistance policy, assessment/mastery authority, evidence semantics, and module provenance.

```text
COURSE / SOURCE MATERIAL
        ↓
VERSIONED COURSE / CONCEPT / PREREQUISITE GRAPH
        ↓
DETERMINISTIC LEARNING CONTROL
        ↓ authorized pedagogical operation
VERSIONED REPRESENTATION REALIZATION
        ↓
GPT LEARNER SURFACE
        ↓
DURABLE OPERATIONAL EVIDENCE
        ↓
DERIVED LEARNER / CONTROLLER STATE
        ↺
```

Issue #63, the P4 PDD/SDD, and ADR-0016 remain the product architecture authority. PIR integration work is subordinate to that authority.

## Proven foundation

### P3 support substrate

Keep protecting:

- durable source-turn capture;
- idempotency/retry safety;
- cross-chat continuity;
- backup/restore;
- doctor/integrity;
- public/private evidence boundaries;
- historical reconciliation only when genuinely new source evidence exists.

Core invariant: **no silent learner-evidence loss**.

### Known canonical PIR integration — PAM A passed

The first known-problem PIR integration is implemented and repo-side assured.

Pinned evidence:

- PR #71 merged;
- merge revision `151c819e3457ae41fa1810b5060d0101f91bc12a`;
- exact tested head `0ccfc9245cc86acdd68587f4bf72158d18ac2070`;
- normal CI: pass;
- PIR Mutation Gate: pass;
- 1268 total mutants / 1064 killed / 204 audited survivors;
- 0 unresolved non-equivalent semantic survivors;
- 0 timeout/other failure statuses.

Do not reopen this assurance claim unless new evidence invalidates it.

## Current execution sequence

### 1. NEXT LOCAL — PAM B

Deploy and validate the known-PIR baseline locally using exact merge revision:

`151c819e3457ae41fa1810b5060d0101f91bc12a`

Required evidence includes:

- pre-deployment revision/runtime/schema/tool inventory;
- backup receipt;
- full local test result;
- doctor/health;
- prior MCP compatibility + PIR operations;
- known sliding-window smoke path;
- restart/resume preserving run identity and pinned revisions;
- retry/idempotency behavior;
- `local_only_changes: []` unless a reusable defect is returned to GitHub and reviewed.

PAM B is independent deployment/reproducibility evidence. Do not add unreviewed pedagogical behavior locally.

### 2. NEXT LIVE — PAM C

Use the existing Study OS GPT against the PAM-B-validated deployment.

Validate:

- known problem resolves to the pinned canonical PIR;
- learner-visible turns are backend-authorized;
- GPT does not independently advance or rewrite critical representation state;
- clarification does not jump progression;
- source-turn durability remains intact;
- terminal historical frontier remains mastery-unproven;
- discrepancies become regression evidence.

PAM C validates product integration, not population learning efficacy.

### 3. PRODUCT-DESIGN FOLLOW-UP — prerequisite-sensitive traversal

Real mutation-testing dogfood exposed a failure before canonical parent assessment: code-first representation could not be parsed, repeated parent explanation did not remediate it, and a simpler concrete/visual boundary representation substantially improved intelligibility.

Treat this as a system/pedagogical routing failure.

Extend the existing #63 architecture to support:

```text
parent concept
→ learner difficulty evidence
→ diagnosis hypothesis
→ prerequisite resolution/probe
→ deterministic parent block
→ authorize smaller_step / change_representation / show_trace
→ versioned prerequisite representation
→ micro-evidence
→ deterministic return to parent
```

Design authority for this delta: `docs/P4_PREREQUISITE_SENSITIVE_TRAVERSAL_DELTA.md`.

Key requirements:

- no parent incorrect outcome when no canonical parent answer was submitted;
- no model-owned prerequisite satisfaction/progression;
- diagnosis remains hypothesis data;
- representation adaptation is a semantic contract, not unconstrained tutor improvisation;
- representation lineage/restoration and module versions remain explicit;
- implementation occurs in a new reviewed revision after the baseline is locally validated, unless PAM B exposes a blocking reusable defect.

### 4. OPERATIONAL IMPROVEMENT LOOP

For meaningful trajectories preserve:

```text
course/problem/node version
learner/controller state before
source representation
learner evidence/attempt
diagnosis hypothesis/version
authorized operation(s)/version
representation version
assistance level
next learner behavior
fade/restoration or prerequisite-return result
transfer/retention where required
module-version set
```

System changes are explicit versions, not silent prompt drift.

Development loop:

```text
real trajectory
→ identify failure
→ reviewed module/policy version N+1
→ deterministic/regression/replay tests
→ prospective real dogfood
→ keep/promote/revert
```

Replay remains counterfactual and never becomes experienced learner evidence.

## Representation architecture direction

The current known-PIR `RepresentationSpec` is intentionally narrow and sufficient for its proven slice. Adaptive representation selection should evolve the P4 contract toward semantic intent, including where relevant:

- representation family;
- semantic roles;
- required relationships;
- required boundary state;
- preserved semantics;
- forbidden complexity;
- code visibility;
- parent/source representation;
- restorable mapping;
- operation and rendering versions.

Candidate families include decision tree, state flow, sequence trace, comparison view, table, source code, and concrete scenario. Do not encode a single theater/ticket analogy as product policy.

## Later — unfamiliar raw-problem compilation

Do **not** enable arbitrary learner-facing raw-problem → PIR compilation merely because PAM A passed or because the mutation-testing trajectory failed.

The eventual architecture should be:

```text
raw unfamiliar task
→ versioned decomposition/compiler prompt
→ schema-constrained candidate concept/prerequisite graph
→ deterministic validation
→ versioned graph
→ deterministic runtime traversal
→ diagnosis/adaptation
→ bounded representation realization
```

For unfamiliar/no-dataset tasks:

- preserve uncertain prerequisite hypotheses;
- record confidence/unresolved status;
- use cheap diagnostic probes where policy allows;
- fail closed for progression claims when a required prerequisite remains unresolved.

The LLM may propose semantic decomposition, candidate prerequisite graphs, diagnosis hypotheses, and representation candidates. It may not own progression, mastery, prerequisite satisfaction, assistance escalation, or canonical learner-state mutation.

## Later — beta/authenticated users

Wait for repeated stable longitudinal trajectories on harder material before prioritizing production multi-user architecture.

Beta validation asks which mechanisms generalize, require personalization, or fail across learners. Subject 001 remains within-learner evidence, not a population proxy.

## Much later — inference-cost/distribution optimization

Preserve replaceable interfaces so validated high-volume functions can later be routed to deterministic or specialized implementations such as:

- rules/state machines;
- parser/AST/compiler transforms;
- deterministic traces/static analysis;
- terminology/identifier transforms;
- templates/retrieval/cache;
- embeddings/small classifiers/models;
- IR/language/notation converters;
- constrained LLM fallback.

Cost optimization follows validated product behavior, not the reverse.

## Deprioritized now

- broad frontend work;
- generic multimodal/video infrastructure;
- production authentication/multi-tenancy;
- broad population research;
- deep FOSSIL integration;
- premature inference-cost optimization;
- unrelated blanket hardening;
- generic live PIR compilation.

## Roadmap governance

Current planning authority is the latest accepted combination of:

- Issue #63;
- P4 PDD/SDD + ADR-0016;
- Issue #66 and its PAM receipts for the known-PIR slice;
- `docs/ROADMAP.md`;
- `docs/CURRENT_STATE.md`;
- `docs/HANDOFF.md`;
- accepted decision records and focused design deltas.

Unchecked historical checklist items do not override newer accepted evidence or explicitly reconciled sequencing.
