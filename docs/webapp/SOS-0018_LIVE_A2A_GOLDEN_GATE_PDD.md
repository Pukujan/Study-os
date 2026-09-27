# SOS-0018 live A2A golden roleplay gate: product/requirements definition (A9b)

Status: planning artifact, issue #126. Evidence: `SOS-0018_LIVE_A2A_GOLDEN_GATE_RESEARCH.md`. Design: `_SDD.md`. Tests: `_TDD.md` and `tests/test_live_a2a_golden_gate_contract.py`. A9b writes docs plus a RED contract only - no product code, no API change, no schema-version change.

## Problem statement

Before any human learner touches the player, we need an automated answer to: "when a live InferHub-backed tutor talks to a realistic learner over the real HTTP player API, does it still teach the golden sliding-window progression, and does it refuse the known failure modes?" Today the closest thing is `tools/run_player_agent_evals.py`, which is an excellent *harness* but is not declared as a *gate*: it has no required persona set, no seed/reliability policy, no pass/fail exit contract, no auditable live receipt, and no explicit statement that a live run must be re-run rather than trusted once. So a green-looking scorecard cannot yet block a merge, and a watcher cannot tell "gate passed" from "someone ran the script casually".

## In scope

- A declared **gate mode** on the existing player A2A harness (`--gate`), producing a machine-readable pass/fail and a non-zero exit on failure.
- A required **persona suite**: golden-path plus adversarial wrong / partial / confused plus a tutor-clarification persona that requests the same concept re-rendered.
- Required **detectors** checked against the golden oracle, including bridges, one-new-concept, no-answer-leak, no-mastery-claim, legal retry/check, stable step identity across re-render, and the A8 typed 1-5 + Submit path.
- **Metamorphic relations** and **hidden holdouts** that fail closed.
- A **live receipt** schema and on-disk path constant, synthetic-only, never `learn.*`.
- The stub-default vs `STUDY_OS_EVAL_LIVE=1` boundary, made explicit in the contract.

## Out of scope (explicit non-goals)

- Any change under `src/` or `web/src/` in A9b. Implementers may add `data-testid`-free harness code only; product changes belong to their own slices.
- Playwright install, browser specs, vision judge wiring: that is SOS-0017 / A9-exec.
- Running a live paid InferHub roleplay in A9b. Documenting the command and env is enough.
- Merging, deploying, or touching https://study.design-bakery.com. Live only after merge to `main`.
- New learner-facing features, new concepts beyond sliding window, curriculum expansion, production UI, generalized recommendation models, universal learning claims (AGENTS.md "Explicitly deferred").
- Promoting synthetic transcripts into learner evidence. Forbidden, permanently.

## Requirements

| Id | Requirement | Rationale (see RESEARCH) |
| --- | --- | --- |
| G1 | The gate must be runnable with zero cost and zero network by default (`StubLLM`), and must reach live InferHub only when `STUDY_OS_EVAL_LIVE=1` **and** `INFERHUB_API_KEY` are present. Missing key with live requested is a hard error, not a silent downgrade. | E9, E7 |
| G2 | The gate must run against a throwaway `TEST_DATABASE_URL` database and must never write scorecards, synthetic transcripts or eval rows into learner evidence (`learn.*`). | E9, manifest prohibited claim |
| G3 | Required persona set, at minimum: `golden`, `wrong_then_right`, `partial_then_right`, `confused_then_right`, `answer_seeker`, `prompt_injector`, `clarify_re_render`. Each persona must be deterministic given `(persona, step_id, attempt)` so detector outcomes are reproducible from seeds. | E1, E3, E5 |
| G4 | `clarify_re_render` must ask for the *same concept shown another way*, and the gate must require the resulting reply to carry a `regenerate_presentation` payload that is a versioned `study-os.player-presentation.v1` update exactly one version past what was served, keeping `step_id`/`concept_id`, actually adopted by the served view, and not moving step/phase/variant. | E3, landed A6/A7 detectors |
| G5 | Detector set must include, at minimum: `MISSING_REQUIRED_BRIDGE`, `BRIDGE_ORDER_VIOLATION`, `FORBIDDEN_CONCEPT_DISCLOSED` (one-new-concept), `ANSWER_REVEAL_FORBIDDEN`, `MASTERY_CLAIM`, `RETRY_SAME_EXAMPLE`, `NO_CONFIRM_AFTER_RETRY`, `MISSING_REGENERATE_PRESENTATION`, `INVALID_REGENERATE_PRESENTATION`, `RENDER_NOT_APPLIED`, `RENDER_MOVED_STEP`, `REVIEW_PATH_VIOLATION`, `INJECTION_ACCEPTED`, `HOLDOUT_NOT_CAUGHT`, `GATE_NOT_LIVE`. | E3, E5, E6 |
| G6 | The gate verdict must be `pass` only if zero blocking detector hits occur on **every** required persona x seed combination. Any single blocking hit is `fail`. No averaging, no tolerance percentage. | E1, E2 |
| G7 | Reliability: with `--seeds N` (N >= 3 for a declared gate run), the gate must report per-persona `pass_count`/`runs` and must fail if any persona is not clean in all runs (a `pass^N` style requirement, not a mean). | E2 |
| G8 | Metamorphic relations must be declared and executed: `MR-replay` (same persona+seed twice yields identical detector outcomes), `MR-rephrase` (semantically equivalent wrong answer still yields the same diagnosis family), `MR-reorder-retry` (retry then correct still requires one more check), `MR-noop` (idle/no-op turn changes no step identity). | E3, E8 |
| G9 | Hidden holdouts must exist and must fail closed: at least one *known-bad* transcript fixture (answer leaked; mastery claimed; re-render text-only) that the detectors must catch. A holdout that the detectors miss is `HOLDOUT_NOT_CAUGHT` and voids the run; the run must not be partially credited. | E3, E8 |
| G10 | A live run must write an auditable receipt (schema `study_os.e2e.live_a2a_gate_receipt/v0.1` at `evals/out/live-a2a-gate-receipt.json`) declaring: run id, wall-clock start/end, `live` boolean, model id(s) actually used, InferHub route, persona x seed verdicts, detector hit counts by code, oracle digest, holdout result, cost and latency p50/p95, and the git commit under test. | E9 |
| G11 | The receipt path must be a declared constant in harness code, and **no receipt may be committed to the repository**. A committed or fabricated receipt must not be able to satisfy the gate. | anti-fabrication (A9a stance) |
| G12 | Stub-default runs must be labelled `live: false` and must be reported as `not_a_live_gate` - never as a passed live gate. A stub run cannot satisfy the live gate requirement for human-test readiness. | E9 |
| G13 | Any LLM judge used is corroborating only: it may add advisory findings, may never flip a deterministic failure to pass, and may never be the sole basis of `pass`. | E4 |
| G14 | Budget guard: a gate run must abort with a clear error if projected turn count exceeds the declared cap (default 4 personas x 3 seeds full suite is fine; a runaway loop must not silently spend). | E9 tiering |
| G15 | Docs, harness and tests must stay consistent: the declared persona list, detector codes, receipt schema id, receipt path constant and gate command must appear verbatim in both SDD and the harness source, so the RED contract can assert them. | local convention |

## Done-when (all must hold)

1. `docs/webapp/SOS-0018_LIVE_A2A_GOLDEN_GATE_{RESEARCH,PDD,SDD,TDD}.md` exist and agree on personas, codes, receipt schema, receipt path and command.
2. `tests/test_live_a2a_golden_gate_contract.py` exists and is the RED contract; it asserts doc presence, the gate command/env markers, the persona set, the detector code set, the receipt schema id and the receipt path constant **as declared in harness code**, and asserts the receipt marker path is absent from the repo.
3. `python -m compileall tests/test_live_a2a_golden_gate_contract.py` and `python -m ruff check tests/test_live_a2a_golden_gate_contract.py` are clean.
4. Before A9b implementation, `python -m unittest tests.test_live_a2a_golden_gate_contract` is **expected RED** and only `test_docs_present` passes.
5. A9-exec/InferHub lands `--gate` in `tools/run_player_agent_evals.py` (or a thin wrapper module it delegates to) with G3-G9, G11, G12, G14 behaviour, flipping the contract green without weakening any assertion.
6. A real live gate run is performed by an executor with `STUDY_OS_EVAL_LIVE=1` and `TEST_DATABASE_URL`, the receipt is stored **outside** the repo (or in a git-ignored artifact path), and the verdict plus run id is posted on #126.
7. No file under `src/` or `web/src/` was changed by A9b, and no `learn.*` evidence was written by any run.
8. `PROJECT_MANIFEST.yaml` / `docs/HANDOFF.md` are updated only if scope, gates, canonical paths, schemas or active risks actually changed (AGENTS.md protocol). A9b itself changes none of them beyond the docs listed.

## Evidence-class impact

| Artifact | Evidence class | Notes |
| --- | --- | --- |
| Live A2A transcripts, detector hits, scorecards, receipts | `derived` system-evaluation data, synthetic only | Never learner evidence; never `learn.*`; kept in `evals/` artifacts outside canonical learner store |
| Observed model ids, routes, costs, latencies | `observed` system telemetry | Recorded for auditability, not for capability claims about the learner |
| Gate verdict posted on #126 | `derived` delivery fact | Cites run id and commit; does not assert human learning outcomes |
| Human session after gate passes | `observed` / `self_reported` learner evidence | Separate capture path, unchanged by this gate |

## Risks

- **Flakiness read as failure.** A stochastic tutor can fail a seed legitimately; G7 makes that visible as `pass_count < runs` instead of hiding it, and the remedy is a filed defect, not more retries.
- **Cost creep.** Mitigated by G1/G14 and by keeping live out of always-on CI.
- **Fabricated receipts.** Mitigated by G11 and by the RED contract asserting the marker path does not exist.
- **Judge laundering.** Mitigated by G13.
- **Over-reading results.** Mitigated by the RESEARCH "does not support" list and by keeping the synthetic-only banner in the scorecard and receipt.
- **Gate drift from docs.** Mitigated by G15 plus the contract asserting verbatim markers.
