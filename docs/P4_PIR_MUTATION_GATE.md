# P4 PIR Implementation Mutation Gate

Tracker: #66

This gate is executable assurance evidence for PAM Checkpoint A. It does not replace the normal Study OS CI suite.

## Scope

Mutation testing is intentionally limited to the production PIR trust kernel:

- `src/study_os/pir/contracts.py`
- `src/study_os/pir/controller.py`
- `src/study_os/pir/registry.py`
- `src/study_os/services/pir_runtime.py`

The mutation runner executes the focused PIR controller/runtime tests:

- `tests/test_pir_teaching_controller.py`
- `tests/test_p4_pir_runtime_integration.py`

Normal CI continues to run the entire repository suite, architecture checks, typing, wheel smoke, and branch coverage.

## Critical failure classes

The gate exists to challenge the implementation around the threats already specified in `P4_PIR_GPT_INTEGRATION_TDD.md`, including:

- incorrect outcome routing or loss of the PARTIAL branch;
- stale-turn bypass;
- missing representation preservation checks;
- renderer/controller oracle leakage;
- terminal mastery-status corruption;
- pinned-revision bypass;
- expansion advancing canonical state;
- idempotency conflicts being accepted as success.

A surviving non-equivalent mutant in one of these critical behaviors blocks PAM Checkpoint A. Equivalent/no-op mutants must be identified explicitly; they are not silently counted as evidence of correctness.

## Reproducibility

The workflow pins `mutmut==3.7.0`, runs from the repository source via `PYTHONPATH=src`, and uploads a JUnit mutation report for inspection.

A green mutation workflow is evidence only for the code and test revision on that exact commit. It does not prove local deployment or live GPT behavior; those remain PAM Checkpoints B and C.
