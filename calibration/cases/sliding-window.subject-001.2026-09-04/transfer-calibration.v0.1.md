# Transfer Calibration v0.1 — September 4 Sliding Window

> Frozen experimental calibration evidence. The JSON sibling is the measured-model input; this file is a human-readable rendering of the same semantic content.

## Identity

- Calibration ID: `sliding-window.subject-001.2026-09-04`
- Artifact: `transfer-calibration` `v0.1`
- Source calibration: `sliding-window-pedagogy-calibration` (2026-09-04)
- Review status: `reviewed_against_canonical_raw_and_reviewed_derivatives`
- Reviewed on: `2026-09-15`
- Authority: `experimental_calibration_evidence_not_runtime_authority`
- Content SHA-256: `4d0014d9baee3dc0c5644ee531ecec8c238a27d7d6b5a5db876b11d38bdd9f53`

## Provenance and isolation

Source manifest: `sessions/2026-09-04/sliding-window-pedagogy-calibration/manifest.json`

Canonical raw evidence, reviewed in order:
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part01.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part02.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part03.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part04.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part05.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part06.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part07.md`
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part08.md`

Corroborating reviewed sources:
- `sessions/2026-09-04/sliding-window-pedagogy-calibration/derived/pedagogy-findings.md`
- `domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md`
- `domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md`

**Measured-teacher boundary:** Raw source paths are provenance only. A measured teacher may receive this frozen artifact, but must never be given or allowed to load the raw transcript contents.

## Modality

- **must** — Hard constraint for a transfer run unless the run is explicitly declared invalid.
- **must_not** — Forbidden behavior for a transfer run.
- **should** — Adaptive default; depart only when visible learner evidence gives a reason.
- **may** — Permitted technique, not a required stage.

## Successful learning trajectory

Status: `historical_evidence_only_not_universal_curriculum`

This preserves the successful Sliding Window dependency sequence as evidence of granularity. Do not copy its vocabulary, constants, or node order into unrelated problems.

### SW-01

- Purpose: Ground the visual object before asking for algorithmic reasoning.
- Historical bridge: Read a short list as visible cells containing values.
- Transfer lesson: Establish what the learner is looking at before introducing relations.

### SW-02

- Purpose: Separate positions from values.
- Historical bridge: Pair visible cells with index labels and practice direct lookup.
- Transfer lesson: Ground labels/coordinates independently before composing them.

### SW-03

- Purpose: Compose one already-grounded lookup with one concrete operation.
- Historical bridge: Select fixed positions and add their visible values.
- Transfer lesson: Use concrete constants before variable notation.

### SW-04

- Purpose: Make state movement visible without changing every representation at once.
- Historical bridge: Move a fixed-width box across the same indexed row.
- Transfer lesson: Keep a stable diagram lineage while changing one relation/action.

### SW-05

- Purpose: Distinguish the moving object's content from its location.
- Historical bridge: Name the box/window positions separately from the values inside them.
- Transfer lesson: Disambiguate object identity, state, and value before formulas.

### SW-06

- Purpose: Derive a relation from grounded examples rather than announce a formula.
- Historical bridge: Relate a concrete start position to the positions covered by the box.
- Transfer lesson: Elicit the pattern from multiple concrete states.

### SW-07

- Purpose: Generalize only after the constant case is stable.
- Historical bridge: Replace concrete indices with i, then introduce k for width.
- Transfer lesson: Introduce one symbol at a time and tie it back to known constants.

### SW-08

- Purpose: Translate grounded semantics into executable structure.
- Historical bridge: Map the understood indexed relation to a loop/code expression.
- Transfer lesson: Code should name operations the learner already understands.

### SW-09

- Purpose: Integrate without discarding prior scaffolding too early.
- Historical bridge: Trace a full example, then fade assistance after correct demonstrations.
- Transfer lesson: Require integration evidence and fade only demonstrated supports.

## Decomposition principles

### DP-01 — `must`

Derive learner-sized prerequisite bridges for the current problem; do not substitute expert-sized algorithm stages for those bridges.

Evidence anchors: `raw parts 01, 03, 08`; `derived F-01/F-02/F-09`

### DP-02 — `should`

Introduce one new semantic relation or action at a time when possible.

Evidence anchors: `raw parts 01, 03`; `derived F-01`

### DP-03 — `must`

Ground an object, term, label, or symbol before asking the learner to use it in a new relation.

Evidence anchors: `raw parts 03, 08`; `derived F-02/F-09`

### DP-04 — `should`

Prefer concrete visible state and action before abstraction, control flow, formulas, or code.

Evidence anchors: `raw parts 01, 08`; `derived F-02/F-11/F-15`

### DP-05 — `should`

When a learner is confused, test for a missing prerequisite or representation bridge before adding more prose.

Evidence anchors: `raw parts 01, 03`; `derived F-09`

### DP-06 — `should`

Skip or compress already-demonstrated prerequisites instead of forcing a fixed sequence mechanically.

Evidence anchors: `raw part 08`; `derived F-12/F-13`

### DP-07 — `must`

Preserve deterministic progression/authority constraints as a control layer; distinguish them from learner-facing decomposition quality.

Evidence anchors: `derived F-13`; `experiments/model-tutoring/HISTORY.md`

## Interaction policy

### IP-01 — `should`

Use a tight cycle: introduce or remind, ask one explicit probe, classify visible evidence, then advance or repair.

Evidence anchors: `raw parts 03, 05`; `derived F-03/F-14`

### IP-02 — `must`

Advance only when the current bridge has adequate visible evidence; turn count is never evidence of mastery.

Evidence anchors: `raw parts 03, 08`; `derived F-03/F-12/F-13`

### IP-03 — `must`

After a wrong or unstable response, correct the smallest failed relation in a grounded representation and then verify recovery.

Evidence anchors: `raw parts 03, 05`; `derived F-03/F-17`

### IP-04 — `must`

A retry must change the example, representation, or operation enough to add information; do not create prompt-only paraphrase loops.

Evidence anchors: `raw part 05`; `derived F-04`

### IP-05 — `should`

Isolate partial success: retain demonstrated suboperations and reteach only the missing relation.

Evidence anchors: `raw parts 05, 08`; `derived F-12`

### IP-06 — `should`

Keep learner-facing replies concise: acknowledge evidence, give the smallest useful explanation, then ask one next question.

Evidence anchors: `raw parts 03, 08`; `derived F-14`

### IP-07 — `must`

Completion must be earned by integrated learner evidence over the required plan bridges, not inferred from a fixed number of exchanges.

Evidence anchors: `derived F-13`; `MT-E001 Phase C`

## Representation policy

### RP-01 — `should`

Keep a stable visual/notation grammar across neighboring exchanges so the learner can compare state changes.

Evidence anchors: `raw parts 03, 05`; `derived F-06`

### RP-02 — `must`

Preserve whitespace/alignment when diagrams, rows, pointers, or code depend on spatial structure.

Evidence anchors: `raw parts 03, 05`; `derived F-06`

### RP-03 — `must_not`

Do not reveal the exact answer, code, pointer, or marked position the learner is currently being asked to produce.

Evidence anchors: `raw parts 05, 08`; `derived F-05/F-07/F-10`

### RP-04 — `should`

Use answer-bearing arrows/cursors in worked examples or corrections, hide them for first-attempt practice when they would reveal the answer, then restore them for review.

Evidence anchors: `raw parts 03, 05`; `derived F-05/F-07`

### RP-05 — `must`

Avoid accidental value/index/name collisions that make distinct concepts look identical; use examples that visibly disambiguate them.

Evidence anchors: `raw part 03`; `derived F-08/F-09`

### RP-06 — `should`

Introduce constants before variables and one variable at a time; every symbol should map back to an already-grounded concrete case.

Evidence anchors: `raw part 08`; `derived F-02/F-15`

### RP-07 — `must`

Any code introduced must map line-by-line or operation-by-operation to semantics already grounded in the conversation.

Evidence anchors: `raw part 08`; `derived F-11`

## Anti-overfit constraints

### AO-01 — `must_not`

Do not copy Sliding Window vocabulary, constants, diagrams, or content into an unrelated algorithm unless independently warranted by that problem.

### AO-02 — `must_not`

Do not treat box, S[i], range(k), window width, or the historical bridge IDs as universal curriculum stages.

### AO-03 — `must`

Infer the target problem's own objects, state, relations, operations, and integration evidence.

### AO-04 — `must`

Transfer decomposition granularity, interaction control, and representation behavior—not the source problem's solution structure.

## Known failure patterns

### KF-01

Large conceptual jumps that require the learner to infer an unstated bridge.

### KF-02

Repeating the same prompt in different words without changing evidence or representation.

### KF-03

Structurally valid language or code that is semantically wrong for the shown state.

### KF-04

Premature formulas, technical terminology, control flow, or code before the underlying objects/relations are grounded.

### KF-05

Repeated confirmation questions that add no information.

### KF-06

Declaring plan completion because a turn target was reached.

### KF-07

Requiring the learner to diagnose or repair a tutor error.

### KF-08

Leaking the requested answer through diagrams, pointers, examples, or code.

### KF-09

Discarding a useful representation before its dependent relation is stable.

### KF-10

Re-teaching already-demonstrated suboperations instead of isolating the failed relation.

## Transfer contract

Teacher may receive:
- this frozen artifact
- the target problem statement and declared variables
- the versioned teacher role/runner contract
- the visible conversation from the current run

Teacher must not receive:
- raw calibration transcript contents
- historical target-problem expected-stage data or regression assertions
- hidden evaluator answers or grading outputs
- prior run transcripts or reviewer comments unless explicitly declared as the changed input

Synthetic student must not receive:
- this calibration artifact
- the generated teaching plan
- hidden solutions
- evaluator rubrics

## Integrity

- Algorithm: `sha256`
- Hash scope: canonical JSON of all top-level fields except integrity; UTF-8; sorted keys; compact separators; ensure_ascii=true
- Content SHA-256: `4d0014d9baee3dc0c5644ee531ecec8c238a27d7d6b5a5db876b11d38bdd9f53`
