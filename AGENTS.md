# AGENTS.md — Study OS Agent Contract

Study OS is currently a **research-first DSA learning harness**, not a general learning product.

Read these files before making substantive changes:

1. `PROJECT_MANIFEST.yaml`
2. `docs/PROJECT_BOUNDARY.md`
3. `docs/RESEARCH_FOUNDATIONS.md`
4. `docs/FAILURE_MODES.md`
5. `docs/RESEARCH_PLAN.md`
6. `docs/FOSSIL_INTEGRATION.md`
7. `docs/HANDOFF.md`
8. the nearest nested `AGENTS.md`, if present

## Non-negotiable project invariants

- Canonical raw learning evidence is immutable after capture.
- Raw/private transcripts do not belong in the public Git repository.
- Keep `observed`, `self_reported`, and `derived` evidence distinct.
- A learner saying “I understand” is not mastery evidence.
- Derived learner-state claims require provenance and uncertainty.
- Subject-specific observations do not automatically become universal lesson/domain claims.
- FOSSIL is an optional promotion/export layer; Study OS canonical learning data must remain usable without FOSSIL.
- Authoritative DSA state/visualization should be deterministic and testable; generative media is not canonical algorithm state.
- Do not build around fixed “learning styles.” Representations are selected based on task, state, and measured outcome.
- Do not expand beyond the current research gate merely because a feature is technically easy to add.

## Current product/research scope

- learner: `subject-001`
- domain: DSA
- language: Python
- first concept family: Sliding Window
- status: pre-build experiment design / Research Gate R0

See `PROJECT_MANIFEST.yaml` for machine-readable state.

## Agent change protocol

For every substantive task:

1. Read the manifest and handoff.
2. Classify the requested change as one or more of:
   - research;
   - schema/data;
   - ingest;
   - lesson/representation;
   - evaluation;
   - infrastructure;
   - FOSSIL export;
   - product/UI.
3. Check the requested work against project boundaries and research gates.
4. Preserve raw evidence and existing semantic versions.
5. Add/update tests for deterministic behavior.
6. If requirements, scope, gates, canonical paths, schemas, or active risks changed, update:
   - `PROJECT_MANIFEST.yaml`
   - `docs/HANDOFF.md`
7. If an architectural/research decision changed, record it in `docs/DECISIONS.md` or a dedicated decision record.
8. Run repository validation/CI-equivalent checks before declaring completion.
9. Report exactly what remains unresolved.

## Handoff protocol

`docs/HANDOFF.md` is a living operational snapshot for the next agent. Keep it concise and current. It must include:

- current phase/gate;
- last meaningful changes;
- active experiment;
- unresolved decisions;
- next recommended tasks;
- known hazards/data-boundary reminders.

Do not turn HANDOFF into history. Git and issues provide history.

## Manifest update protocol

`PROJECT_MANIFEST.yaml` is the machine-readable source for project status and guardrails.

Update it when any of these change:

- current research gate;
- active learner/domain/concept;
- schema versions;
- canonical storage paths;
- required CI checks;
- FOSSIL integration policy;
- build/deployment status;
- major open risks;
- next research milestone.

Agents may update the manifest, but must never silently relax a project invariant. A relaxation requires an explicit decision record and should be surfaced to the user.

## Data handling

This repository is public.

- Full raw transcripts: local/private evidence store by default.
- Public repo: hashes, manifests, redacted fixtures, schemas, reviewed/curated derived records.
- Do not commit secrets, account identifiers, private conversation exports, or hidden evaluation answers.
- Hidden transfer/eval material should be separated from tutor-visible content when possible.

## Research integrity

Prefer behavioral evidence over impression:

1. deterministic correctness/tests;
2. unaided behavior;
3. transfer;
4. delayed retention;
5. self-report;
6. model-derived interpretation.

Self-report is valuable but is not automatically causal evidence.

When comparing interventions, record confounds and avoid implying causality when multiple variables changed.

## DSA pedagogy contract

Teach and measure translation between:

`problem -> recognition -> mental model -> state -> invariant -> procedure -> pseudocode -> code -> debugging -> transfer`

Prefer semantic operations before syntax memorization.

Initial learning operations include:

- expand;
- decompose;
- trace;
- predict;
- explain;
- contrast;
- abstract;
- specialize;
- reconstruct;
- debug;
- translate;
- fade;
- transfer.

## Build/test expectations

Until a package layout is formalized, the minimum checks are defined in `.github/workflows/ci.yml` and `tools/validate_repo.py`.

Expected local checks:

```bash
python -m compileall tools tests
python tools/validate_repo.py
python -m unittest discover -s tests -v
```

If dependencies are later added, update this file and CI together.

## Pull request expectations

A substantive PR should state:

- research/product question addressed;
- data/schema impact;
- evidence class affected;
- tests performed;
- research gate impact;
- known limitations;
- whether manifest/handoff changed.

## Explicitly deferred

Until Research Gate R0 passes, do not prioritize:

- production UI;
- CD/deployment;
- full DSA curriculum;
- video/image generation pipelines;
- generalized learner recommendation models;
- universal learning claims.
