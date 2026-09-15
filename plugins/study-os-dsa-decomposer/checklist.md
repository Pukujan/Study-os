# Study OS DSA decomposer review checklist

Checklist version: `study-os-dsa-decomposer-checklist.v1`

Use after `plugins/study-os-dsa-decomposer/skill.md` generates a candidate plan and before learner-visible tutoring begins.

This checklist is an acceptance surface, not a prompt for inventing missing content. If an item fails, reject/revise the candidate plan.

## Algorithm model

- [ ] The plan contains an actual solution model, not merely topic labels.
- [ ] Primitive objects are explicit.
- [ ] State that must persist is explicit.
- [ ] Every state variable/symbol has one stable meaning.
- [ ] At least one invariant or equivalent stable semantic constraint is explicit where the algorithm requires one.
- [ ] One-step transition/recurrence/pointer update/queue update/etc. is explicit.
- [ ] Terminal/base behavior is explicit.
- [ ] Empty/unreachable behavior is explicit when relevant.
- [ ] The integrated algorithm can be derived from the model without an unexplained leap.

## Backward dependency quality

- [ ] Every non-primitive learner-facing relation has prerequisite nodes.
- [ ] No prerequisite edge points forward to something not yet grounded.
- [ ] The graph includes representation bridges, not only conceptual nouns.
- [ ] Structurally complex problems are not compressed into a few ungrounded macro stages.
- [ ] The graph is not fragmented into meaningless microsteps merely to increase node count.
- [ ] Algorithm complexity and teaching complexity are represented separately when they differ.

## Representation choice

- [ ] Candidate representations were considered when materially different choices exist.
- [ ] The selected representation preserves the algorithm's important invariants.
- [ ] The selected representation minimizes unnecessary decoding/bridge cost for the calibrated learner.
- [ ] Grounded symbolic/algebraic/state-transition reasoning is preferred when it actually simplifies the structure.
- [ ] No universal equation-first assumption is present.
- [ ] Rejected representation families have compact reasons when the rejection matters to reproducibility.

## Vocabulary and symbols

- [ ] New technical terms have simple accurate grounding where helpful.
- [ ] Canonical term introduction occurs after or with grounding, not before meaning.
- [ ] Learner-facing symbols are defined before use in a relation.
- [ ] The same object is not renamed casually across the plan.
- [ ] A simple metaphor does not erase an important property (for example, queue ordering).
- [ ] Vocabulary optimizes semantic accuracy before simplicity.
- [ ] No turn requires an avoidable pile-up of new technical terms/relations without explicit justification.

## Learner evidence and correction

- [ ] Every required node has a concrete evidence condition.
- [ ] Evidence is satisfiable from actual learner behavior, not hidden corpus labels.
- [ ] Correct-but-tentative responses can be distinguished from concept failure.
- [ ] Meaningful errors require changed retry when appropriate.
- [ ] Independent verification is required after an error exposed instability when policy says so.
- [ ] Assistance ceilings are explicit.
- [ ] Elaboration/representation repair can occur without illegal advancement.

## Tutor integrity

- [ ] The learner never needs to discover algorithmic misinformation for the plan to recover.
- [ ] The learner never needs to repair a variable/symbol meaning change.
- [ ] The learner never needs to police skipped prerequisites.
- [ ] Tutor semantic/representation/dependency violations are rejectable as system failures.
- [ ] The plan contains no hidden benchmark answer/oracle material supplied only for evaluation.

## Completion

- [ ] Completion requires every required learning node or equivalent required evidence.
- [ ] Completion requires terminal/base behavior.
- [ ] Completion requires integrated algorithm evidence.
- [ ] Completion cannot be inferred from turn count.
- [ ] Anti-loop budget exhaustion is failure/diagnostic, never success.
- [ ] A conversation that remains on concept zero through the entire budget necessarily fails.

## Provenance and prompt versioning

- [ ] Decomposition prompt version is present.
- [ ] Decomposition prompt SHA-256 hash is present.
- [ ] Model identifier is present.
- [ ] TeachingPlan schema version is present.
- [ ] Run ID and source problem identity are present.
- [ ] Historical prompt versions were not overwritten.

## Hidden holdout boundary

For promotion/holdout runs:

- [ ] Engineering/prompt-fixing agent cannot read the holdout directory.
- [ ] Measured decomposer receives only the hidden problem statement needed for the run.
- [ ] Measured teacher/student receive no evaluator oracle.
- [ ] Measured agents cannot modify the frozen candidate prompts/code/schema.
- [ ] Holdout evaluator has read-only candidate access and private oracle access.
- [ ] Evaluator output to engineering is sanitized and does not reveal raw hidden content.
- [ ] If a hidden case is revealed for debugging, it is marked burned and moved to public regression before further tuning.

## Final decision

A candidate plan may enter tutoring only if all applicable required items pass schema/deterministic validation. Human/model reviewer judgment may add stricter findings, but may not waive failed semantic or provenance requirements.
