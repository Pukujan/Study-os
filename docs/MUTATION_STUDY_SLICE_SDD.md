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
