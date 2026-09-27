# Mutation-Testing Study Slice — PDD

## Problem

Study OS needs a small real-world dogfood slice for learning a technically complex topic through decomposition, probes, representation continuity, and durable evidence.

The first topic is mutation testing. The slice must be usable locally by Luna while a separate engineering session works on PR #71.

## Product hypothesis

A learner can build transferable understanding of mutation testing through a dependency-ordered concept graph with short explanations, concrete code examples, prediction probes, corrective feedback, and explicit progress evidence.

This slice tests the Study OS learning loop; it does not claim that the intervention is effective beyond this learner/session.

## Learner outcome

Given an unfamiliar mutation-testing diff/report, the learner should be able to distinguish killed vs survived mutants, weak vs strong test oracles, meaningful vs equivalent mutations, semantic vs diagnostic survivors, mutation score vs release assurance, and appropriate mutation-testing use around AI-system authority boundaries.

## First vertical slice

The slice contains five dependency-ordered probes:

1. survivor meaning;
2. oracle strength;
3. equivalent mutants;
4. release-policy interpretation;
5. transfer to an AI/runtime authority invariant.

Each probe is deterministic multiple choice. Luna/ChatGPT may teach and explain freely, but the local adapter owns progression and evidence.

## User experience

Luna starts or resumes a run, asks the current probe through the ChatGPT conversation, records the learner's final option, reads the deterministic outcome, explains/corrects as needed, continues to the next probe, and periodically displays a progress chart from adapter status.

## Persistence

Use a dedicated SQLite database for this experimental slice. Do not alter the production Study OS schema in the first experiment.

Persist run identity/current node, every submitted response, assistance level, deterministic outcome, and per-node attempts/correct/mastered state.

## Integrity constraints

- LLM does not decide whether an answer is correct.
- Incorrect answers do not advance.
- Invalid choices do not write evidence.
- Restart/resume preserves state and attempts.
- A completed run cannot silently return to active.
- No modification to PR #71 or its mutation-gate branch.
- No claim of mastery from exposure alone.

## Success criteria

Automated tests must prove deterministic progression, fail-closed invalid input, incorrect-response non-advance, durable SQLite evidence across restart, exact completion after all five correct probes, and reconstructable per-node progress.

## Deferred

Production MCP additions, production DB migration, free-text LLM grading, FSRS scheduling, delayed retention, and a general lesson compiler.


## Practical-first curriculum amendment

The learner-facing course is approximately 75-80% practical and 20-25% theory. Theory follows observation rather than preceding it.

Every lab uses this loop:

1. understand a small product rule;
2. predict a realistic failure;
3. inspect or run a mutation;
4. observe whether tests detect it;
5. strengthen the test or classify the survivor;
6. extract the formal mutation-testing concept;
7. transfer it once to a related system.

The product progression is:

- Cloud API rate limiter: quota-boundary mutation -> killed/survived and oracle strength.
- Idempotent cloud job: duplicate execution -> stateful semantic mutants.
- Circuit breaker: threshold mutation -> temporal/state-machine testing.
- Feature rollout gate: boolean mutation -> cohort isolation and blast radius.
- ML deployment gate: weakened metric policy -> deterministic ML release assurance.
- LLM tool authorization: weakened permission/approval gate -> AI authority boundaries.
- Study-OS capstone: stale-turn mutation -> survivor classification and release policy.

Do not begin with mutation-operator taxonomy or mutation-score mathematics. Introduce terminology only after the learner has encountered the concrete failure it explains.

The capstone should use a Study-OS-style authority invariant and require the learner to classify the survivor and propose the behavioral test that should kill it.
