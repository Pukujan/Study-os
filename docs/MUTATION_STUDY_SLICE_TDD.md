# Mutation-Testing Study Slice — TDD

## Contract tests

CT1 — Starting a run creates an active run at survivor_meaning and returns the canonical first probe.

CT2 — A legal wrong choice records one incorrect attempt and leaves the run on the same node.

CT3 — An invalid option raises an error and writes no attempt/progress mutation.

CT4 — A correct choice advances exactly one node and marks the submitted node mastered.

CT5 — A later process can reconstruct the same current node and accumulated progress from SQLite.

CT6 — After correct answers for all five probes, run status is complete, current node is null, every node is mastered, and attempts remain preserved.

CT7 — A completed run rejects new responses.

CT8 — Only A0-A4 assistance levels are accepted and the chosen level is preserved.

## Validation

Run:

python -m unittest tests.test_mutation_study_slice

Then smoke the separate-process path with:

python tools/mutation_study_slice.py start --db /tmp/mutation-study.sqlite --subject-id subject-001
python tools/mutation_study_slice.py respond --db /tmp/mutation-study.sqlite --run-id RUN --choice B --assistance-level A0
python tools/mutation_study_slice.py status --db /tmp/mutation-study.sqlite --run-id RUN

The smoke succeeds only if later processes see state written by earlier processes.
