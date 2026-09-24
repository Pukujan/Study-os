# TASK-SOS-0001 — Helper adoption: Study OS owns its continuity state

<!-- continuity:task {"acceptance":["continuity preflight --root <Study-os> at the pinned PCM commit prints MODE: TARGET_VALID","schemas/v1/** is byte-identical to PCM schemas/v1 at the pinned commit",".content-system/system-version.json pins the CGM repository, version, and full commit, and the pinned CGM validator result is recorded including any remaining gap","AGENTS.md states Study OS is authoritative and the helpers are pinned tooling only","validate_repo.py, the engineering baseline, and the full unittest suite stay green, plus a new offline adoption test","no private-repository content is copied"],"depends_on":[],"goal":"Make Pukujan/Study-os the validated owner of its continuity and human-facing content state, using PCM (mature-repository overlay) and CGM (pinned target adapter) as pinned helpers only.","id":"SOS-0001","issue_url":"https://github.com/Pukujan/Study-os/issues/78","next_action":"Review the PR for #78; after merge and confirmed checks, mark SOS-0001 completed and clear the continuity:current active task in docs/HANDOFF.md.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor session on task/SOS-0001-helper-adoption","priority":"P2","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"active","why":"Existing Study OS documents already own project facts, but nothing machine-checkable declared that ownership or pinned the helper repositories, so agents could treat helper state, chat, or moving helper main branches as authority."} -->

- Status: active
- Owner: Pukujan (GitHub assignee)
- Priority: P2
- Depends on: none
- Branch: `task/SOS-0001-helper-adoption`
- GitHub issue (leaf): #78 — parent: none — dependencies: none

## Goal

Make Pukujan/Study-os the validated owner of its continuity and human-facing content state, using PCM (mature-repository overlay) and CGM (pinned target adapter) as pinned helpers only.

## Why

Existing Study OS documents already own project facts, but nothing machine-checkable declared that ownership or pinned the helper repositories, so agents could treat helper state, chat, or moving helper main branches as authority.

## Human outcome

A fresh agent or collaborator opening Study OS can tell, and mechanically check, that this repository owns its project state; that `docs/PROJECT_CHARTER.md`, `docs/HANDOFF.md`, and `tasks/` are the canonical PROJECT, CURRENT, and TASK records; and that PCM and CGM are consulted only at pinned revisions.

## Allowed files

- `.continuity/config.json`, `schemas/v1/**` (exact PCM copy), `tasks/**`
- `docs/PROJECT_CHARTER.md` and `docs/HANDOFF.md`: marker line plus a short continuity section only
- `.content-system/**`
- `AGENTS.md`, `PROJECT_MANIFEST.yaml`, `docs/DECISIONS.md` (D015), `.gitignore`
- `tests/test_helper_adoption.py`

## Scope and boundaries

- In scope: PCM overlay, CGM adapter pin, ownership rules, offline adoption test. A CI step running the pinned PCM validator is prepared but not committed: the available GitHub token lacks the `workflow` scope needed to push workflow changes.
- Out of scope: runtime, MCP, domain schema, or migration changes; README rewrite; generated imagery (deferred until R0); repository settings such as branch protection or auto-merge; any content from private repositories.
- Dependencies/uncertainty: PCM's GitHub progression contract expects required CI plus auto-merge; Study OS `main` currently has neither branch protection nor auto-merge enabled. That is a repository-settings decision for the owner and is not changed here.

## Acceptance criteria

- [ ] `continuity preflight --root .` at PCM `0b3be9ca80da816de4621ac4e85612990084216e` prints `MODE: TARGET_VALID`.
- [ ] `schemas/v1/**` byte-identical to that PCM commit.
- [ ] `.content-system/system-version.json` pins CGM `0.4.0` at `f85e88bc00362c53061d95ac7811bd9c6ada8e32`; the pinned CGM validator result is recorded, including the remaining gap.
- [ ] `AGENTS.md` states Study OS is authoritative and helpers are pinned tooling only.
- [ ] Existing checks stay green, plus `tests/test_helper_adoption.py`.
- [ ] No private-repository content is copied.

## Evidence and sources

- PCM adoption contract: [`docs/TARGET_ADOPTION.md` @ 0b3be9c](https://github.com/Pukujan/project-continuity-modules/blob/0b3be9ca80da816de4621ac4e85612990084216e/docs/TARGET_ADOPTION.md)
- CGM adapter contract: [`README.md` "Try it" @ f85e88b](https://github.com/Pukujan/content-generation-modules/blob/f85e88bc00362c53061d95ac7811bd9c6ada8e32/README.md) and [`docs/MIGRATING_TO_0.4.md`](https://github.com/Pukujan/content-generation-modules/blob/f85e88bc00362c53061d95ac7811bd9c6ada8e32/docs/MIGRATING_TO_0.4.md)
- Starting revision: Study OS `main` @ `151c819e3457ae41fa1810b5060d0101f91bc12a`.

## Related records

- Leaf issue #78; parent: none; dependencies: none.
- Primary writer / branch: Grok Bot executor session / `task/SOS-0001-helper-adoption`; source issue revision: #78 as created 2026-09-24; as-of status: implementation pushed, PR review pending.
- PR/CI evidence and push receipt: posted on #78 after push.

## Checkpoint log

## Handoff

Read `docs/PROJECT_CHARTER.md` → `docs/HANDOFF.md` → this task → `AGENTS.md` "Helper modules and project ownership". Checkpoint before stopping.
