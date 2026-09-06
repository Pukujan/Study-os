# P4 PIR Implementation Mutation Gate

Tracker: #66

This gate is executable assurance evidence for PAM Checkpoint A. It does not replace the normal Study OS CI suite or the pedagogical data/specification mutation suite.

## Scope

`mutmut` is intentionally limited to callable production PIR trust-kernel code:

- `src/study_os/pir/contracts.py`
- `src/study_os/pir/controller.py`
- `src/study_os/services/pir_runtime.py`

The focused mutation runner executes:

- `tests/test_pir_teaching_controller.py`
- `tests/test_p4_pir_runtime_integration.py`

`src/study_os/pir/registry.py` is deliberately not in the `mutmut==3.7.0` file target. The registry constructs the reviewed canonical asset at module import. During the first mutation run, mutmut's trampoline stack recorder attempted to resolve the synthetic caller path `<frozen importlib._bootstrap>` with `strict=True` and failed before any mutant could execute. Treating that runner crash as mutation evidence would be false assurance.

Registry and canonical-asset behavior remain mechanically protected by deterministic asset validation plus the explicit pedagogical data/specification mutations required by `P4_PIR_GPT_INTEGRATION_TDD.md`. The mutmut lane challenges the callable implementation authority points; it does not replace those fixture-level mutation tests.

Normal CI continues to run the entire repository suite, architecture checks, typing, installed-wheel smoke, and branch coverage.

## Critical failure classes

The gate exists to challenge implementation around the threats already specified in `P4_PIR_GPT_INTEGRATION_TDD.md`, including:

- incorrect outcome routing or loss of the PARTIAL branch;
- stale-turn bypass;
- missing representation-preservation checks;
- renderer/controller oracle leakage;
- terminal mastery-status corruption;
- pinned-revision bypass;
- expansion advancing canonical state;
- idempotency conflicts being accepted as success.

A surviving non-equivalent mutant in one of these critical behaviors blocks PAM Checkpoint A. Equivalent/no-op mutants must be identified explicitly; they are not silently counted as evidence of correctness.

## Fail-closed result policy

The workflow pins `mutmut==3.7.0` and does not rely on the exit code of `mutmut run`, because that command may finish successfully with surviving mutants.

After mutation execution it records:

- `mutmut-results.txt` from `mutmut results --all`;
- `mutants/mutmut-cicd-stats.json` from `mutmut export-cicd-stats`.

`tools/check_pir_mutation_results.py` then requires:

- at least one measured mutant;
- at least one killed mutant;
- complete accounting of every mutant;
- `survived = 0`;
- `no_tests = 0`;
- `skipped = 0`;
- `suspicious = 0`;
- `timeout = 0`;
- `check_was_interrupted_by_user = 0`;
- `segfault = 0`.

Missing/corrupt stats, a runner failure, or any unresolved mutation status therefore fails the gate.

A green mutation workflow is evidence only for the code and test revision on that exact commit. It does not prove local deployment or live GPT behavior; those remain PAM Checkpoints B and C.
