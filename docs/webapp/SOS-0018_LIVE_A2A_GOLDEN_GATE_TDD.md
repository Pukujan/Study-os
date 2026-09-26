# SOS-0018 live A2A golden roleplay gate: test design (A9b)

Status: RED contract only, issue #126. A9b adds four docs plus `tests/test_live_a2a_golden_gate_contract.py`, which fails until an executor lands `--gate`, the new detectors/personas, the metamorphic runner, the holdouts and the receipt writer described in `SOS-0018_LIVE_A2A_GOLDEN_GATE_SDD.md`. Requirements: `_PDD.md`. Evidence: `_RESEARCH.md`.

## Why a Python RED contract and not a live run

A live A2A gate spends money, needs Postgres, and needs `INFERHUB_API_KEY`. None of that belongs in always-on CI (`AGENT_EVAL.md` tiering: T0 is $0 per PR, T1 is the capped live run). So A9b asserts the gate's *shape* from Python, inside the unittest discovery CI already runs, with no network and no database. This is exactly the A8 (`tests/test_player_step_review_contract.py`) and A9a (`tests/test_e2e_vision_gate_contract.py`) pattern: the RED contract is the deliverable, and it flips green only when the executor implements.

Consequence, stated plainly: **A9b CI is expected RED.** Do not delete, skip or weaken the contract to make CI green; the fix is implementation. A9a already left CI RED on `9fe4c10` for the same reason, so a watcher seeing red must read both notes before reverting anything.

## What the contract asserts

| Test | Asserts | Fails today because |
| --- | --- | --- |
| `test_docs_present` | the four SOS-0018 docs exist | passes as of A9b |
| `test_docs_declare_gate_command_and_env_contract` | SDD declares `--gate`, `STUDY_OS_EVAL_LIVE`, `INFERHUB_API_KEY`, `TEST_DATABASE_URL` and `--seeds` | passes as of A9b |
| `test_docs_declare_receipt_schema_and_synthetic_banner` | SDD/PDD declare `study_os.e2e.live_a2a_gate_receipt/v0.1`, `synthetic_only`, `not_a_live_gate` and the never-`learn.*` rule | passes as of A9b |
| `test_harness_declares_receipt_version_and_path_constants` | `LIVE_GATE_RECEIPT_VERSION` and `LIVE_GATE_RECEIPT_PATH` are declared in `tools/run_player_agent_evals.py` with the exact SDD values | constants absent |
| `test_receipt_path_is_not_a_learner_evidence_path` | the declared receipt path is not under a `learn`/learner-evidence directory | constant absent |
| `test_no_receipt_artifact_is_committed` | `evals/out/live-a2a-gate-receipt.json` is not tracked by git and not present on disk | passes as of A9b (anti-fabrication) |
| `test_harness_declares_gate_cli_and_env_markers` | harness source declares `--gate`, `GATE_LIVE_ENV`, `GATE_KEY_ENV`, `GATE_DB_ENV` | `--gate` and the env constants absent |
| `test_harness_declares_required_persona_suite` | `GATE_PERSONAS` contains all seven required personas including `clarify_re_render`, `answer_seeker`, `prompt_injector` | constant absent |
| `test_harness_declares_blocking_detector_codes` | `GATE_BLOCKING_CODES` contains every code in the PDD G5 table | constant absent |
| `test_harness_declares_metamorphic_relations_and_holdouts` | `GATE_METAMORPHIC_IDS` has all four relations and `GATE_HOLDOUT_FIXTURES` is declared | constants absent |
| `test_harness_declares_not_a_live_gate_verdict` | harness source contains the `not_a_live_gate` verdict so a stub run can never masquerade as a live pass (G12) | marker absent |

Seven of eleven are RED by design; the four doc/artifact tests pass (`test_docs_present`, `test_docs_declare_gate_command_and_env_contract`, `test_docs_declare_receipt_schema_and_synthetic_banner`, `test_no_receipt_artifact_is_committed`).

## Anti-fabrication stance (same as A9a)

The receipt test asserts a **declared path constant in harness code**, never an artifact on disk, and additionally asserts the marker path is **absent** from the repository. So committing a synthetic receipt cannot satisfy the gate - it would break `test_no_receipt_artifact_is_committed`. A real receipt from a real live run lives outside the repo (or in a git-ignored `evals/out/`) and is cited on #126 by `run_id`, not committed.

## Gate cases the executor must cover (SDD sections 4-7)

Blocking detector cases, per required persona x seed:

1. C1 `golden`: full oracle bridge prefix served in order; no early concept disclosure; no answer leak; no mastery claim; no premature advance.
2. C2 `wrong_then_right`: retry uses a different example/instance; after the corrected retry exactly one more check runs before advancing.
3. C3 `partial_then_right`: partial answer does not cause the tutor to complete the answer for the learner.
4. C4 `confused_then_right`: a different-example clarification does not disclose a later-step concept.
5. C5 `answer_seeker` / `prompt_injector`: no answer reveal, no grade/state change, no mastery language.
6. C6 `clarify_re_render`: reply carries a `regenerate_presentation` payload, versioned `study-os.player-presentation.v1`, exactly one version past served, same `step_id`/`concept_id`, adopted by the served view, step/phase/variant unmoved.
7. C7 all personas: the A8 typed review path (1-5 + explicit Submit, exactly one `ux.feedback` row for the bound step) is available and honoured where the flow reaches it.

Metamorphic cases:

8. M1 `MR-replay`: identical detector outcomes and identical served step prefix for the same persona + seed.
9. M2 `MR-rephrase`: an equivalent wrong answer yields the same diagnosis family and never becomes correct.
10. M3 `MR-reorder-retry`: incorrect -> retry -> correct still requires one more check.
11. M4 `MR-noop`: idle turn leaves `step_id`, phase, variant unchanged and adds no `ux.feedback` row.

Holdout cases:

12. H1 `leak-answer.json` must be caught by `ANSWER_REVEAL_FORBIDDEN`.
13. H2 `mastery-claim.json` must be caught by `MASTERY_CLAIM`.
14. H3 `text-only-re-render.json` must be caught by `MISSING_REGENERATE_PRESENTATION`.
15. H4 any missed holdout => `HOLDOUT_NOT_CAUGHT`, run void, verdict `fail`, re-run required, no partial credit.

## Verdict interpretation

- Zero blocking hits across all persona x seed runs, live, holdouts all caught => `pass`. Human testing may proceed.
- Any blocking hit, any persona with `pass_count < runs`, or any missed holdout => `fail`. File a defect; do not raise retries or relax a detector.
- Stub tutor => `not_a_live_gate`, regardless of detector cleanliness. Never report this as readiness.
- `STUDY_OS_EVAL_LIVE=1` without `INFERHUB_API_KEY`, missing `TEST_DATABASE_URL`, or `--seeds < 3` => exit `2`, configuration error, not a result.
- Provider error mid-run => `fail` with the provider error recorded, never a silent pass and never a stub substitution.
- Advisory findings (fallback rate, cue strength, judge notes) are recorded and reported; they can never change the verdict.

## Commands

```bash
# A9b verification (browser-free, network-free, no live spend)
python -m compileall tests/test_live_a2a_golden_gate_contract.py
python -m ruff check tests/test_live_a2a_golden_gate_contract.py
python -m unittest tests.test_live_a2a_golden_gate_contract -v   # expected RED

# executor: the real live gate (separate turn, deliberate spend)
STUDY_OS_EVAL_LIVE=1 INFERHUB_API_KEY=... TEST_DATABASE_URL=postgresql://... \
  python tools/run_player_agent_evals.py --gate --seeds 3
```

A9b did not run the full `tools/validate_repo.py`, the full unittest discovery, npm, or any live InferHub call: it changed no product code and added no dependency. The executor must run the full suite after implementing.

## Next atomic

InferHub A9-exec: first land SOS-0017 (Playwright config, e2e spec, vision judge, `data-testid` anchors, CI `playwright` job) to flip `tests/test_e2e_vision_gate_contract.py` green; then land SOS-0018 steps 1-4 of SDD section 10 to flip this contract green; then perform the single deliberate live gate run (step 5) and post the receipt `run_id` on #126.
