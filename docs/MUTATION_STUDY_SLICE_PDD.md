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
