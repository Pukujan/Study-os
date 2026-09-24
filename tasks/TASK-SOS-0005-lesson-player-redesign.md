# TASK-SOS-0005 — Lesson Player Redesign

<!-- continuity:task {"acceptance":["Task file, branch, HANDOFF marker, draft PR using Refs #101 only","Micro-step lesson player: 1-3 sentence screens with interactive/animated visuals (fraction bars/area models; box/index array with moving window)","Learner answers by typing, predicting or manipulating the visual; MCQ only where it fits","Always-available tutor chat grounded in current step and history, re-explains in a different representation, never leaks answers during assessment, routed through rules -> Jev (OpenRouter) -> glm-5.3/deepseek (InferHub), every decision logged","I'm confused and wrong answers trigger an adaptive re-explanation (smaller step or visual)","Step map/progress; clean mobile-first design","HESI fractions golden-style draft note (pending Alex's review); DSA sliding-window flow checked against goldens and conformance oracle, check recorded","Screenshots at 1280x800 and 390x844 under /workspace/ux-shots (box)","Existing tests green; new tests for re-explanation triggers, no answer leak during assessment, step rendering","Checkpoint receipts on #101; not merged to main or deployed until Alex approves"],"depends_on":[],"goal":"Redesign the web lesson player as a prototype for Alex's approval: golden-faithful micro-steps, interactive visuals, always-available grounded tutor chat, adaptive re-explanation; screenshots; not merged or deployed until approved.","id":"SOS-0005","issue_url":"https://github.com/Pukujan/Study-os/issues/101","next_action":"study goldens/PIR/specs/research, then implement player + API","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0005-lesson-player-redesign","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"active","why":"Alex found the live HESI fractions lesson to be a wall of text plus a 4-option MCQ with no LLM interaction, no visuals, no adaptive re-explanation, and no match to the transcript/goldens."} -->

- Status: active
- Owner: Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0005-lesson-player-redesign
- Priority: P1
- Depends on: none
- Branch: `task/SOS-0005-lesson-player-redesign`
- GitHub issue (leaf): #101, parent #82 (web-app epic); dependencies: none

## Goal

Redesign the web lesson player as a prototype for Alex's approval: golden-faithful micro-steps, interactive visuals, always-available grounded tutor chat, adaptive re-explanation; screenshots; not merged or deployed until approved.

## Why

Alex found the live HESI fractions lesson to be a wall of text plus a 4-option MCQ with no LLM interaction, no visuals, no adaptive re-explanation, and no match to the transcript/goldens.

## Allowed files

- `web/**`, `src/study_os/web/**`, `tests/test_web_*.py`
- `domains/hesi/**` (draft golden note), `docs/webapp/**` (prototype notes, conformance check record)
- `docs/HANDOFF.md` (marker + short note), `tasks/TASK-SOS-0005-lesson-player-redesign.md`

## Human outcome

Alex can see and judge (via screenshots and a local run) a lesson player that teaches the way the goldens do: one small idea per screen, a visual, learner produces before being told, real tutor chat, and adaptive re-explanation.

## Scope and boundaries

- In scope: prototype player + API (steps, re-explain, chat), fractions golden-style draft, DSA faithful rendering, screenshots, tests.
- Out of scope: merge to main, production deploy, other HESI topics, learner memory (#88).
- Dependencies/uncertainty: Alex's approval of design and fractions draft; LLM quality of re-explanations.

## Acceptance criteria

- [ ] Task file, branch, HANDOFF marker, draft PR using Refs #101 only
- [ ] Micro-step lesson player: 1-3 sentence screens with interactive/animated visuals (fraction bars/area models; box/index array with moving window)
- [ ] Learner answers by typing, predicting or manipulating the visual; MCQ only where it fits
- [ ] Always-available tutor chat grounded in current step and history, re-explains in a different representation, never leaks answers during assessment, routed through rules -> Jev (OpenRouter) -> glm-5.3/deepseek (InferHub), every decision logged
- [ ] I'm confused and wrong answers trigger an adaptive re-explanation (smaller step or visual)
- [ ] Step map/progress; clean mobile-first design
- [ ] HESI fractions golden-style draft note (pending Alex's review); DSA sliding-window flow checked against goldens and conformance oracle, check recorded
- [ ] Screenshots at 1280x800 and 390x844 under /workspace/ux-shots (box)
- [ ] Existing tests green; new tests for re-explanation triggers, no answer leak during assessment, step rendering
- [ ] Checkpoint receipts on #101; not merged to main or deployed until Alex approves

## Evidence and sources

Link repository state at a revision and cite external factual claims directly. Record commands and results for claims that need verification.

## Reproduction details (only when needed)

Starting revision, material inputs/configuration, runtime, exact command or prompt, observed result, and limitations.

## Related records

- Leaf #101; parent #82; dependencies none.
- Primary writer: Grok Bot executor / `task/SOS-0005-lesson-player-redesign` / from main `8d4417b` / active
- Related PR/CI evidence and push receipt (request ID / SHA):

## Checkpoint log

No checkpoints yet.

### 2026-09-24 23:02:39 UTC — Grok Bot executor

<!-- continuity:checkpoint {"agent":"Grok Bot executor","blocked":[],"changed":["none"],"completed":["issue #101 opened as sub-issue of #82; task file; branch; HANDOFF marker"],"decisions":["no new decisions"],"evidence":["no external evidence recorded"],"next_action":"study goldens/PIR/specs/research; draft PR","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0005","timestamp":"2026-09-24T23:02:39Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"a3ad02f3743d8b6edce82a5969b590c6f522e563879441cbfbf34bd908aed0f6","request_id":"9169688110f54545b3d3fd42ea25e4c9","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0005"} -->

Completed:
- issue #101 opened as sub-issue of #82; task file; branch; HANDOFF marker

Evidence:
- no external evidence recorded

Decisions:
- no new decisions

Changed:
- none

Blocked/uncertain:
- none

Next:
- study goldens/PIR/specs/research; draft PR

## Handoff

Read PROJECT → CURRENT → this task → minimum relevant spec. Checkpoint before stopping.
