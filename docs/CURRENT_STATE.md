# Current State

Date: 2026-09-03
Status: P4 deterministic learning controller + representation engine
Primary tracker: #63

## Current product reality

Study OS is actively used through the GPT app for real learning.

The source-turn durability and cross-chat continuity work is operational for normal longitudinal use. Historical recovery of the user-authorized transcript source has also completed successfully. P3 now remains supporting infrastructure rather than the product-development center.

Canonical live learner state/evidence remains local:

```text
/root/.study-os
SQLite + private evidence store
```

GitHub remains architecture/spec/contracts/tests/public-safe lineage, not the live learner database.

## Accepted historical recovery state

The published historical recovery source was reconstructed and hash-verified, preserved as immutable local evidence, reviewed, and reconciled into `subject-001`.

Accepted receipt:

- source Markdown SHA-256: `07becb3c24c2876354dd496ba57e1832df23763eda7b4c85b19891e77b7b5a7d`;
- 34 reviewed outer turns accepted and backfilled;
- 50 nested/embedded headings ignored rather than double-counted;
- second reconciliation added zero turns;
- existing attempts/events/assessments/checkpoints remained unchanged;
- message/artifact/on-disk hashes passed;
- backup/restore and doctor passed;
- source evidence exhausted for this export;
- original ChatGPT conversation completeness remains `NOT_ESTABLISHED`.

See `docs/HISTORICAL_TRANSCRIPT_RECOVERY_RECEIPT.md`.

No further recovery from this exact source is required. Additional recovery is warranted only if a stronger/new source provides genuinely missing evidence.

## Current product thesis

Study OS addresses the mismatch between a learner and the representation chosen by a course/source author.

Difficulty may come from:

- the target concept itself;
- a missing prerequisite;
- terminology/identifier interference;
- notation or source wording;
- code/control-flow representation;
- amount of context/information;
- task decomposition/granularity;
- assistance level.

The product should use AI to adapt the representation while deterministic code/state controls curriculum progression and allowed teaching behavior.

```text
course/source
→ deterministic course state
→ deterministic learning controller
→ authorized pedagogical operation
→ versioned representation engine
→ GPT learner surface
→ durable learner response
→ deterministic outcome/state transition
```

## Early operational evidence

The recovered historical sequence around dictionaries/Two Sum exposed a useful product-discovery pattern:

- the variable name `seen` conflicted with the learner's prior association with sets;
- `index_by_num` remained confusing;
- neutral `box` terminology was self-reported as clearer;
- a subsequent dictionary lookup was answered correctly.

Interpretation boundary:

- **observed:** confusion persisted before the intervention and a later lookup answer was correct;
- **self-reported:** `box` was clearer;
- **derived/proposed:** identifier semantic interference may have contributed;
- **not proven:** renaming alone caused the improvement.

The intervention also simplified/decomposed the task, so representation change and decomposition must remain separate first-class variables.

## Current architectural priority

Define and implement the smallest real deterministic learning-control loop.

The system must make every learner-facing teaching action reconstructable as:

```text
course node/version
+ learner-control state
+ evidence
→ controller authorization
→ operation(s)/version
→ representation/version
→ bounded AI response
→ learner outcome
→ deterministic next state
```

The AI is allowed to generate/transform under an authorized operation. It is not allowed to silently advance curriculum or mark mastery.

## Current design authority

- Issue #63
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_PDD.md`
- `docs/P4_DETERMINISTIC_LEARNING_CONTROLLER_SDD.md`
- `docs/ADR-0016-deterministic-learning-control.md`
- `docs/ROADMAP.md`
- latest accepted entries in `docs/DECISIONS.md`

## Current semantic objects to stabilize

P4.0 focuses on contracts for:

- course node/version;
- prerequisite/progression policy;
- learner-control state;
- pedagogical operation/version;
- diagnosis hypothesis/version;
- representation/version + reversible mapping;
- controller decision;
- assistance level/ceiling;
- module-version set;
- learner outcome;
- offline replay evaluation.

These semantic objects may reuse existing runtime tables. New schema should be additive only where existing data cannot express the required invariants.

## Operational improvement loop

Now that sessions can persist across chats, real learning should continuously improve the system through versioned data rather than hidden prompt edits.

```text
real trajectory
→ immutable source evidence
→ normalized operation/outcome
→ identify controller/representation failure
→ module version N+1
→ offline replay
→ prospective dogfood
→ keep/promote/revert
```

Replay is counterfactual system evaluation. It is never recorded as if the learner actually experienced the candidate intervention.

## Longitudinal target

Continue learning through progressively harder material:

```text
Python/DSA foundations
→ LeetCode-style problems
→ complex DSA
→ system design
→ AI-system reasoning/debugging
```

Increasing task complexity is a feature of the development process: it should expose where the controller's diagnosis, decomposition, representation, assistance, restoration, or progression policy breaks.

Within-learner trajectories are valuable product evidence but not population-level proof.

## Later expansion

After repeated stable trajectories exist on harder material, beta/authenticated users can test which mechanisms generalize and which need personalization.

Production multi-user architecture is not a current requirement.

## Long-horizon cost direction

Do not optimize inference cost now. Preserve interfaces that later allow LLM-backed modules to be replaced or front-routed by:

- parsers/AST/compiler transforms;
- deterministic traces/static analysis;
- terminology/identifier rewriting;
- retrieval/cached validated representations;
- sentence embeddings/transformers;
- small classifiers/task-specific models;
- templates/IR transforms;
- constrained LLM fallback.

The stable asset is the controller/representation contract and operational data, not any particular model implementation.

## Supporting P3 state

Keep protecting:

- durable source-turn capture;
- idempotent retry semantics;
- cross-chat continuity;
- backup/restore;
- doctor/integrity;
- future reconciliation if genuinely new historical source evidence appears;
- structured curriculum provenance.

Core invariant remains:

> No silent learner-evidence loss.

## Immediate execution priorities

1. Accept/freeze P4 PDD/SDD and decision invariants.
2. Audit the current runtime/schema against P4 contracts.
3. Reuse existing durable data structures wherever semantics align.
4. Design only the smallest additive migration/data changes required.
5. Implement one real current course-node deterministic loop.
6. Bound GPT behavior with explicit course state + learner state + authorized operation.
7. Record exact decision/representation/module versions and subsequent outcomes.
8. Continue normal learning and extend the system from observed failures.
