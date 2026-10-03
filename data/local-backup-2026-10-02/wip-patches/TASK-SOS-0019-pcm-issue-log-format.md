# TASK-SOS-0019 — PCM issue-log-format marker and task-projection closeout

<!-- continuity:task {"acceptance":["AGENTS.md carries the issue-log-format 1.2.0 block (START/END markers, pcm:policy line, guidance text) copied verbatim from the pinned PCM CLI, with no existing policy rewritten","tasks/TASK-SOS-0014-mascot-locomotion.md is status completed with real acceptance criteria and a checkpoint entry","No additional Git worktree exists outside <canonical-root>/pcm/worktree/<TASK-ID>","continuity validate --root . returns VALID with no errors and no warnings","continuity preflight --root . returns MODE: TARGET_VALID","python -m unittest discover -s tests -v passes"],"depends_on":[],"goal":"Continuity hygiene: satisfy the PCM 0.6.0 issue-log-format check and bring task projections and worktree layout back to VALID","id":"SOS-0019","issue_url":"https://github.com/Pukujan/Study-os/issues/175","next_action":"Open PR from task/SOS-0019-pcm-issue-log-format with the AGENTS.md and task-file changes; run the pinned validator; merge","owner":"Pukujan (GitHub assignee); primary writer: [CC] on task/SOS-0019-pcm-issue-log-format","priority":"P3","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"active","why":"PCM CLI 0.6.0 validate reports a missing issue-log-format policy marker in AGENTS.md plus three worktrees outside the canonical checkout (2026-09-27)"} -->

- Status: active
- Owner: Pukujan (GitHub assignee); primary writer: [CC] on task/SOS-0019-pcm-issue-log-format
- Priority: P3
- Depends on: none
- Branch: `task/SOS-0019-pcm-issue-log-format`
- GitHub issue (leaf): #175, parent: none; dependencies: none

## Goal

Continuity hygiene: satisfy the PCM 0.6.0 issue-log-format check and bring task projections and worktree layout back to VALID

## Why

PCM CLI 0.6.0 `validate` reports a missing issue-log-format policy marker in `AGENTS.md` plus three worktrees outside the canonical checkout (2026-09-27). The marker check is new in 0.6.0 and the pin landed via #128/#129, so this is the follow-through.

## Allowed files

- `AGENTS.md`
- `tasks/TASK-SOS-0014-mascot-locomotion.md`, this task file
- `docs/HANDOFF.md` (only if a projection update is required)

## Human outcome

A maintainer running the pinned continuity validator sees `VALID` with no warnings, so a real violation is not buried in known noise.

## Scope and boundaries

- In scope: the issue-log-format guidance block in `AGENTS.md`, the SOS-0014 task projection, and the worktree layout.
- Out of scope: any product or UI change; anything from #126; moving the PCM pin (already at `c18bfd60`); repairing the three pre-existing Windows line-ending/artifact test failures (separate issue).

## Acceptance criteria

- [ ] `AGENTS.md` carries the issue-log-format 1.2.0 block (START/END markers, `pcm:policy` line, guidance text) copied verbatim from the pinned PCM CLI, with no existing policy rewritten
- [ ] `tasks/TASK-SOS-0014-mascot-locomotion.md` is `status: completed` with real acceptance criteria and a checkpoint entry
- [ ] No additional Git worktree exists outside `<canonical-root>/pcm/worktree/<TASK-ID>`
- [ ] `continuity validate --root .` returns `VALID` with no errors and no warnings
- [ ] `continuity preflight --root .` returns `MODE: TARGET_VALID`
- [ ] `python -m unittest discover -s tests -v` passes

## Evidence and sources

- Leaf issue #175 — https://github.com/Pukujan/Study-os/issues/175
- Pin provenance: #128 / PR #129, merge commit `838bae6e89be7a677cb4c62f95a5d6fcbad7a692`
- Canonical marker source: pinned PCM CLI `c18bfd6064d1249996bc00c45dbbc6721ec5dfd9`, `ISSUE_LOG_FORMAT_GUIDANCE`
- Numbering note: SOS-0017 and SOS-0018 are already used by the E2E + cheap-vision gate lineage (`docs/webapp/SOS-0017_E2E_VISION_GATE_*.md`), so this task is SOS-0019.

## Handoff

Read PROJECT → CURRENT → this task → minimum relevant spec. Checkpoint before stopping.
