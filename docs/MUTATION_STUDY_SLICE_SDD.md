# Mutation-Testing Study Slice — SDD

## Architecture

ChatGPT / Luna conversation -> local mutation-study adapter -> deterministic lesson graph / transition policy -> dedicated SQLite evidence DB.

The conversational model owns explanation and wording. The adapter owns canonical probe IDs, legal choices, correctness, progression, and persistence.

## Module

src/study_os/experimental/mutation_study.py

Public operations:

- start_run(db_path, subject_id)
- get_turn(db_path, run_id)
- submit_choice(db_path, run_id, choice, assistance_level)
- get_status(db_path, run_id)

CLI adapter: tools/mutation_study_slice.py

Commands: start, next, respond, status. All CLI output is JSON so Luna can consume it without parsing prose.

## Lesson graph

survivor_meaning -> oracle_strength -> equivalent_mutant -> release_policy -> ai_authority_transfer -> complete

Wrong answers remain on the current node. Correct answers advance exactly one node.

## SQLite schema

study_runs stores run_id, subject_id, lesson_id, current_node_id, status, created_at, updated_at.

study_attempts stores attempt_id, run_id, node_id, choice, outcome, assistance_level, created_at.

study_progress stores run_id, node_id, attempts, correct, mastered.

## Transition invariants

- status is active or complete;
- active run always references a known node;
- only correct response advances;
- final correct response sets current_node_id to null;
- invalid run/choice/assistance fails before insertion;
- assistance levels are A0 through A4.

## Returned turn

A turn includes run_id, lesson_id, status, node_id, concept, prompt, legal choices, and a lightweight representation sequence. Luna may render that representation as prose, Mermaid, or a ChatGPT chart without changing progression semantics.

## Versioning

Lesson ID is mutation-testing.v0. Semantic changes to answer keys or graph order require a new lesson revision.


## Tutor presentation contract

The adapter remains deterministic, while Luna presents each node as a small systems lab.

For each canonical node Luna should present, in order:

- the product/system context;
- a compact implementation or state diagram;
- a concrete failure/mutation;
- a prediction or debugging task;
- the canonical probe;
- adapter-authoritative feedback;
- only after a correct answer, a short theory extraction;
- one sentence connecting the result to the next system.

Target pacing is 75-80% practical interaction and 20-25% theory/explanation.

Curriculum contexts, in order:

1. cloud API rate limiting;
2. idempotent distributed jobs;
3. circuit breaker/retry state;
4. feature rollout policy;
5. ML model deployment gate;
6. LLM tool authorization/evidence gate;
7. Study-OS authority survivor capstone.

The SQLite evidence model remains unchanged. Practical lab presentation is a tutor-layer concern and must not give Luna authority to alter canonical correctness or progression.
