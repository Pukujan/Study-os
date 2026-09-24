# TASK-SOS-0002 — Sliding-window PIR lesson follows the two goldens

<!-- continuity:task {"acceptance":["The main path of the shipped asset introduces exactly the golden relations in golden order, one per step (problem, position, index, box_size_k, box_start_i, window_sum, successive_sums, recurrence_repetition, enumerate, append)","Every probe routes correct -> why on the same chart, wrong -> correction with reassurance -> retry on a different example -> one more check, and partial -> keep the correct part and ask only for the missing step","The box chart (numbers, index row, box, k) is present in every recurrence and append step, and exercise charts omit answer-revealing components (arrows, highlights, the enumerate pair row, the append form)","No learner-visible text claims mastery, and the only exit is assembled_mastery_unproven","tests/test_pir_golden_conformance.py kills each benchmarker-style violation class with a targeted mutation","Full local CI equivalent is green, the PIR mutation gate tests pass, and the required checks pass on the PR"],"depends_on":[],"goal":"Rebuild the shipped sliding-window PIR lesson so it follows the two goldens under domains/dsa/sliding-window/golden/ step by step, scoped to what they cover (through enumerate and append), with deterministic conformance tests mirrored from study-os-benchmarker.","id":"SOS-0002","issue_url":"https://github.com/Pukujan/Study-os/issues/80","next_action":"None for SOS-0002. Verify PR #81 merged with required checks and that #80 has a closing receipt; start the parts 06-08 loop-assembly work from a new issue with its own reviewed golden.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor session on task/SOS-0002-sliding-window-golden-lesson","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"completed","why":"The shipped lesson (about 20 steps) started at sum[i]. It skipped position, zero-based index, k, the box, and moving i, then jumped to the recurrence without concrete successive sums, and it dropped the array, index, and box in the code steps. That contradicts learner-calibrated goldens Study OS already owns, and nothing mechanical detected the drift."} -->

- Status: completed
- Owner: Pukujan (GitHub assignee)
- Priority: P1
- Depends on: none (SOS-0001 / #78 merged)
- Branch: `task/SOS-0002-sliding-window-golden-lesson`
- GitHub issue (leaf): #80 — parents: #63 (P4 controller tracker), #65 (PIR / golden compilation) — dependencies: none

## Goal

Rebuild the shipped sliding-window PIR lesson so it follows the two goldens step by step:

- `domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md`
- `domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md`

Scope is limited to what those goldens cover, which ends at `enumerate(a)` and `append`.

## Why

The shipped lesson (`sep4.sliding-window.production-known-problem.v1`, 20 steps) started at `sum[i]`. It skipped position `p`, zero-based index `i = p - 1`, box size `k`, the box itself, and `i` moving the box. It jumped from `sum[i]` to the recurrence without the concrete successive sums or the repetition from `S[0]`. In the code steps, the chart was replaced by `problem_anchor` / `code` / `variable_roles`. `first_window` and `boundary` were explain-only, and the lesson ended by showing the full loop.

## Human outcome

A learner who starts the known sliding-window problem gets the same progression the learner calibrated on 2026-09-04: one picture, one new relation, and one tiny question per step. The same box chart stays in view into the code steps. Wrong answers are corrected on the chart with reassurance, then retried on a different example and checked once more. Partial answers keep what was right. The lesson stops at the golden boundary, without claiming mastery.

## Allowed files

- `src/study_os/pir/registry.py`, `src/study_os/pir/sliding_window.py` (new), `src/study_os/pir/conformance.py` (new)
- `domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json` (new), `domains/dsa/sliding-window/README.md`
- `tests/test_pir_golden_conformance.py` (new). PIR tests that encode the old step path: `tests/test_p4_pir_runtime_integration.py`, `tests/test_pir_critical_mutations.py`, `tests/test_pir_mutation_authority.py`, `tests/test_pir_mutation_semantics.py`, `tests/test_pir_mutation_contract_edges.py`
- `tasks/**`, `docs/HANDOFF.md` (marker only), `docs/DECISIONS.md` (D016)

## Scope and boundaries

- In scope: the canonical asset, a conformance evaluator that mirrors `Pukujan/study-os-benchmarker` at `d438988fda12e9df902caabbcb6a639834452d5d` (`specs/VERIFICATION.md` BINV-001..005, `evaluator.py`, `decomposition.py`), an oracle for this lesson, and tests.
- Out of scope: controller, contracts, runtime, schema, and MCP changes; the mutmut target list (`pyproject.toml` references files, not steps, so it is unchanged); any private-repository content.
- Revision: `canonical_pir_revision` is now `sep4.sliding-window.golden-box-index-enumerate-append.v2`, and `renderer_revision` is now `study-os.markdown-renderer.v1`. Problem runs pinned to v1 fail closed on the existing revision check (integrity error), so no v1 step id is ever routed through v2.

## Step list

Before (v1, 20 steps): `problem_anchor`, `sum_probe`, `sum_partial`, `arithmetic_probe`, `sum_wrong`, `recurrence_bridge`, `recurrence_probe`, `recurrence_repair`, `enumerate_bridge`, `enumerate_probe`, `enumerate_repair`, `append_bridge`, `append_probe`, `append_repair`, `max_bridge`, `max_probe`, `max_repair`, `first_window`, `boundary`, `final_loop`.

After (v2): 326 steps generated from 10 golden concepts. Step ids are `<concept>.intro`, `<concept>.e<example>.n<correct answers still needed>` with `.why` / `.fix`, and `.partial` / `.finish` for partial answers. All-correct main path (19 probes):

| Golden step | Concept | Probes on the correct path |
|---|---|---|
| G1 step 0 | `problem` (problem and `a`) | none (explain only) |
| G1 step 1 | `position` | position of 6 → 4; position of 1 → 5 |
| G1 step 2 | `index` (`i = p - 1`) | index of 6 → 3; index of 9 → 5 |
| G1 step 3 | `box_size_k` | `k = 5` → 4 7 2 6 1; `k = 2` → 4 7 |
| G1 step 4 | `box_start_i` | `i = 1, k = 2` → 7 2; `i = 3, k = 2` → 6 1 |
| G1 step 5 | `window_sum` | `sum[i=2]`, `k = 3` (box shown) → 9; `sum[i=2]`, `k = 2` (no box) → 8, partial `2 6` |
| G2 step 1 | `successive_sums` | `sum[i+1]` → 14; `sum[i+2]` → 8; `sum[i+3]` → 14 |
| G2 step 2 | `recurrence_repetition` (from `S[0]`, `j = k - 1`) | `S[1]` → 14; `S[2]` → 8 |
| G2 step 3 | `enumerate` | `a = 6` → (3, 6); `a = 8` in `[5, 2, 8, 4, 7, 1]` → (2, 8) |
| G2 step 4 | `append` | `S[i] = S[i-1] + a[i]`; `S[i] = S[i-1] + num` |
| (boundary) | `frontier.assembled` | exit `assembled_mastery_unproven` |

## Acceptance criteria

- [x] Main path introduces exactly the golden relations in golden order, one per step.
- [x] Every probe follows the golden correct / wrong / partial feedback rules.
- [x] The box chart is present in recurrence and append steps, and exercise charts omit answer-revealing components.
- [x] No mastery claim, and the only exit is `assembled_mastery_unproven`.
- [x] Conformance tests kill each violation class with a targeted mutation.
- [x] Local CI equivalent green; required checks green on the PR.

## Follow-up (not implemented here; parts 06-08 of the public 2026-09-04 session)

The goldens stop at `append` and say the next concept is to "combine these pieces into the actual Python loop one piece at a time". The public transcript parts 06-08 under `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/` and the benchmarker fixtures (`max-sum-vertical`, `s0-to-si`, `max-loop`, `combined-loop`, `arbitrary-k-first-window`, `final-combined-loop`) cover those steps. They need a reviewed golden before they ship:

1. Loop assembly: place `S.append(...)` inside `for i, num in enumerate(a):` one piece at a time.
2. `max`: `max_sum = S[0]` from the first box, then `S[0]` to `S[i]` when `i = 0`, then the comparison `if S[i] > max_sum: max_sum = S[i]`.
3. The `else` bridge: first box (`i == 0`) versus later boxes.
4. Stop condition: a box cannot start after `len(a) - k` (`if i > len(a) - k: break`).
5. `range(k)`: build the first box for any `k` with `for x in range(k): S[i] = S[i] + a[i+x]`, keeping the same `S[i]`.
6. Final combined-loop exposure only after all of the above are grounded, still without a mastery claim.

Other follow-ups:

- Golden 2 rule 12 allows accepting a short phone answer such as `S.append(...)` when the intent is clear. A deterministic classifier cannot judge intent, so v2 treats it as incorrect and shows the full canonical answer. It accepts the value-only answer as partial.
- Golden 1 step 0 asks "Are you ready?". The controller has no readiness probe, so v2 shows the problem statement and moves straight to position.
- Examples cycle after repeated errors (for example, `position.e0` can come back after three misses). A larger example bank would remove repeats.

## Evidence and sources

- Goldens (sha256 pinned in the oracle): `87ee6091…` (G1), `97ece0d1…` (G2).
- Benchmarker rules: [`specs/VERIFICATION.md` @ d438988](https://github.com/Pukujan/study-os-benchmarker/blob/d438988fda12e9df902caabbcb6a639834452d5d/specs/VERIFICATION.md), [`evaluator.py`](https://github.com/Pukujan/study-os-benchmarker/blob/d438988fda12e9df902caabbcb6a639834452d5d/src/study_os_benchmarker/evaluator.py), [`decomposition.py`](https://github.com/Pukujan/study-os-benchmarker/blob/d438988fda12e9df902caabbcb6a639834452d5d/src/study_os_benchmarker/decomposition.py). Rules are mirrored, not vendored. Representation vocabulary follows the public `successive-sums` and `enumerate-vertical` fixtures.
- Starting revision: Study OS `main` @ `b227f51d93451aa688bd3c5a707f11f5df39cbf2`.

## Related records

- Leaf issue #80; parents #63 and #65; dependencies: none.
- Primary writer / branch: Grok Bot executor session / `task/SOS-0002-sliding-window-golden-lesson`.
- PR/CI evidence and push receipts: posted on #80.

## Checkpoint log

### 2026-09-24 21:37:15 UTC — Grok Bot executor (for Pukujan)

<!-- continuity:checkpoint {"agent":"Grok Bot executor (for Pukujan)","blocked":["PR CI (required checks) and the PIR mutation gate workflow have not run yet."],"changed":["src/study_os/pir/registry.py","src/study_os/pir/sliding_window.py","src/study_os/pir/conformance.py","domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json","domains/dsa/sliding-window/README.md","tests/test_pir_golden_conformance.py","tests/test_p4_pir_runtime_integration.py, tests/test_pir_critical_mutations.py, tests/test_pir_mutation_authority.py, tests/test_pir_mutation_semantics.py, tests/test_pir_mutation_contract_edges.py","tasks/TASK-SOS-0002-sliding-window-golden-lesson.md","docs/HANDOFF.md","docs/DECISIONS.md"],"completed":["Rebuilt the canonical sliding-window asset from the two goldens (src/study_os/pir/sliding_window.py): 10 golden concepts, 326 generated steps, 19 probes on the all-correct path, exit assembled_mastery_unproven.","Added src/study_os/pir/conformance.py and domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json mirroring study-os-benchmarker d438988, plus tests/test_pir_golden_conformance.py (31 tests).","Updated PIR tests that encoded the v1 step path (first-probe answer and all-correct walks) without changing controller, contracts, runtime, or mutmut targets."],"decisions":["Scope stops at enumerate and append as in the goldens; loop assembly, max, else bridge, stop condition, and range(k) are recorded as follow-up in the task file.","Enumerate charts follow the golden and the benchmarker enumerate fixtures (no window box, no pair row in exercises); every recurrence and append step keeps the box chart.","canonical_pir_revision moves to sep4.sliding-window.golden-box-index-enumerate-append.v2 so v1-pinned runs fail closed instead of being routed through new step ids."],"evidence":["Product commit ae4227a on task/SOS-0002-sliding-window-golden-lesson, based on main b227f51.","Local CI equivalent on Python 3.13: dependency lock, contract inventory, curriculum policy, schema render check, compileall, validate_repo, PCM 0b3be9c preflight TARGET_VALID, engineering baseline, ruff, pyright 0 errors, wheel smoke pass; unittest 381 OK (350 before + 31 new); branch coverage 85% (gate 70%). Python 3.11.16: unittest 381 OK."],"next_action":"Open the PR for #80 with auto-merge; after required checks pass and it merges, post the closing receipt, mark SOS-0002 completed, and clear the continuity:current active task.","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0002","timestamp":"2026-09-24T21:37:15Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"3a1e4f8b15cb88284760f9c6c4eb5603c1561c5d7c1b6aafc1c081651d0e8b30","request_id":"sos-0002-cp1-20260924","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0002"} -->

Completed:
- Rebuilt the canonical sliding-window asset from the two goldens (src/study_os/pir/sliding_window.py): 10 golden concepts, 326 generated steps, 19 probes on the all-correct path, exit assembled_mastery_unproven.
- Added src/study_os/pir/conformance.py and domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json mirroring study-os-benchmarker d438988, plus tests/test_pir_golden_conformance.py (31 tests).
- Updated PIR tests that encoded the v1 step path (first-probe answer and all-correct walks) without changing controller, contracts, runtime, or mutmut targets.

Evidence:
- Product commit ae4227a on task/SOS-0002-sliding-window-golden-lesson, based on main b227f51.
- Local CI equivalent on Python 3.13: dependency lock, contract inventory, curriculum policy, schema render check, compileall, validate_repo, PCM 0b3be9c preflight TARGET_VALID, engineering baseline, ruff, pyright 0 errors, wheel smoke pass; unittest 381 OK (350 before + 31 new); branch coverage 85% (gate 70%). Python 3.11.16: unittest 381 OK.

Decisions:
- Scope stops at enumerate and append as in the goldens; loop assembly, max, else bridge, stop condition, and range(k) are recorded as follow-up in the task file.
- Enumerate charts follow the golden and the benchmarker enumerate fixtures (no window box, no pair row in exercises); every recurrence and append step keeps the box chart.
- canonical_pir_revision moves to sep4.sliding-window.golden-box-index-enumerate-append.v2 so v1-pinned runs fail closed instead of being routed through new step ids.

Changed:
- src/study_os/pir/registry.py
- src/study_os/pir/sliding_window.py
- src/study_os/pir/conformance.py
- domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json
- domains/dsa/sliding-window/README.md
- tests/test_pir_golden_conformance.py
- tests/test_p4_pir_runtime_integration.py, tests/test_pir_critical_mutations.py, tests/test_pir_mutation_authority.py, tests/test_pir_mutation_semantics.py, tests/test_pir_mutation_contract_edges.py
- tasks/TASK-SOS-0002-sliding-window-golden-lesson.md
- docs/HANDOFF.md
- docs/DECISIONS.md

Blocked/uncertain:
- PR CI (required checks) and the PIR mutation gate workflow have not run yet.

Next:
- Open the PR for #80 with auto-merge; after required checks pass and it merges, post the closing receipt, mark SOS-0002 completed, and clear the continuity:current active task.

## Closeout (2026-09-24, Grok Bot executor for Pukujan)

Owner-authorized closeout. This is not a `continuity checkpoint` run, because that command only records checkpoints for active tasks.

- CI on the checkpoint head `429b84c`: [run 36062662414](https://github.com/Pukujan/Study-os/actions/runs/36062662414). `Validate research harness` passed, including the pinned PCM preflight, and `Python 3.11 compatibility` passed. The PIR mutation gate, [run 36062662431](https://github.com/Pukujan/Study-os/actions/runs/36062662431) (`Kill critical PIR mutants`), also passed.
- Status set to completed. The `continuity:current` active task is cleared in `docs/HANDOFF.md`.
- Still open: the follow-up list above (parts 06-08, the append shorthand, the readiness probe, and the example bank). The merge SHA and the state of #80 are recorded on #80, not here (receipt-only transitions).

## Handoff

Read `docs/PROJECT_CHARTER.md` → `docs/HANDOFF.md` → this task → the two goldens → `src/study_os/pir/sliding_window.py`. Run `python -m unittest tests.test_pir_golden_conformance` after any lesson change.
