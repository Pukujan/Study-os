# TASK-SOS-0001 — Helper adoption: Study OS owns its continuity state

<!-- continuity:task {"acceptance":["continuity preflight --root <Study-os> at the pinned PCM commit prints MODE: TARGET_VALID","schemas/v1/** is byte-identical to PCM schemas/v1 at the pinned commit",".content-system/system-version.json pins the CGM repository, version, and full commit, and the pinned CGM validator result is recorded including any remaining gap","AGENTS.md states Study OS is authoritative and the helpers are pinned tooling only","validate_repo.py, the engineering baseline, and the full unittest suite stay green, plus a new offline adoption test","no private-repository content is copied"],"depends_on":[],"goal":"Make Pukujan/Study-os the validated owner of its continuity and human-facing content state, using PCM (mature-repository overlay) and CGM (pinned target adapter) as pinned helpers only.","id":"SOS-0001","issue_url":"https://github.com/Pukujan/Study-os/issues/78","next_action":"None for SOS-0001. Verify PR #79 merged with required checks and that #78 is closed with a closing receipt; start the next issue-backed task separately.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor session on task/SOS-0001-helper-adoption","priority":"P2","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"completed","why":"Existing Study OS documents already own project facts, but nothing machine-checkable declared that ownership or pinned the helper repositories, so agents could treat helper state, chat, or moving helper main branches as authority."} -->

- Status: completed
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

- In scope: PCM overlay, CGM adapter pin, ownership rules, offline adoption test, and a CI step that runs the pinned PCM validator (added in `ec2cd66` after the token gained the `workflow` scope).
- Out of scope: runtime, MCP, domain schema, or migration changes; README rewrite; generated imagery (deferred until R0); repository settings such as branch protection or auto-merge; any content from private repositories.
- Dependencies/uncertainty: PCM's GitHub progression contract expects required CI plus auto-merge. On 2026-09-24, with owner authorization, repository auto-merge was enabled and `main` protection was set to require `Validate research harness` and `Python 3.11 compatibility` on up-to-date branches (no required reviews, admins not enforced). These settings live on GitHub, not in this file.

## Acceptance criteria

- [x] `continuity preflight --root .` at PCM `0b3be9ca80da816de4621ac4e85612990084216e` prints `MODE: TARGET_VALID`.
- [x] `schemas/v1/**` byte-identical to that PCM commit.
- [x] `.content-system/system-version.json` pins CGM `0.4.0` at `f85e88bc00362c53061d95ac7811bd9c6ada8e32`; the pinned CGM validator result is recorded, including the remaining gap.
- [x] `AGENTS.md` states Study OS is authoritative and helpers are pinned tooling only.
- [x] Existing checks stay green, plus `tests/test_helper_adoption.py`.
- [x] No private-repository content is copied.

## Evidence and sources

- PCM adoption contract: [`docs/TARGET_ADOPTION.md` @ 0b3be9c](https://github.com/Pukujan/project-continuity-modules/blob/0b3be9ca80da816de4621ac4e85612990084216e/docs/TARGET_ADOPTION.md)
- CGM adapter contract: [`README.md` "Try it" @ f85e88b](https://github.com/Pukujan/content-generation-modules/blob/f85e88bc00362c53061d95ac7811bd9c6ada8e32/README.md) and [`docs/MIGRATING_TO_0.4.md`](https://github.com/Pukujan/content-generation-modules/blob/f85e88bc00362c53061d95ac7811bd9c6ada8e32/docs/MIGRATING_TO_0.4.md)
- Starting revision: Study OS `main` @ `151c819e3457ae41fa1810b5060d0101f91bc12a`.

## Related records

- Leaf issue #78; parent: none; dependencies: none.
- Primary writer / branch: Grok Bot executor session / `task/SOS-0001-helper-adoption`; source issue revision: #78 as created 2026-09-24; as-of status: completed; closeout commit pushed to PR #79, merge pending at this commit (live result on #78).
- PR/CI evidence and push receipt: posted on #78 after push.

## Checkpoint log

### 2026-09-24 20:50:25 UTC — Grok Bot executor (for Pukujan)

<!-- continuity:checkpoint {"agent":"Grok Bot executor (for Pukujan)","blocked":["Pinned PCM preflight is not yet a CI step: adding it to .github/workflows/ci.yml needs a push with the workflow scope (snippet in the PR description).","CGM adapter validation stays incomplete until the owner approves a first reviewed Study OS visual or an asset exemption in CGM.","Required CI and auto-merge are not configured on main."],"changed":[".continuity/config.json","schemas/v1/**","tasks/TASK-SOS-0001-helper-adoption.md",".content-system/**","AGENTS.md","PROJECT_MANIFEST.yaml","docs/PROJECT_CHARTER.md","docs/HANDOFF.md","docs/DECISIONS.md",".gitignore","tests/test_helper_adoption.py"],"completed":["Adopted PCM via the mature-repository overlay: .continuity/config.json (prefix SOS, GitHub issue authority, managed-worktrees), exact schemas/v1 copy, project marker in docs/PROJECT_CHARTER.md, current marker in docs/HANDOFF.md, tasks/ with this issue-backed task.","Pinned CGM 0.4.0 at f85e88bc00362c53061d95ac7811bd9c6ada8e32 as a .content-system adapter with project-brief v2 claims pinned to Study OS 151c819.","Recorded ownership rules in AGENTS.md, helper pins in PROJECT_MANIFEST.yaml (0.2.4), decision D015, and tests/test_helper_adoption.py."],"decisions":["Canonical PROJECT is docs/PROJECT_CHARTER.md and CURRENT is docs/HANDOFF.md because the YAML manifest cannot carry the line marker; PROJECT_MANIFEST.yaml remains the machine-readable status source.","Do not fabricate a visual asset to satisfy the CGM validator; record the gap instead.","Do not change repository settings: PCM expects required CI plus auto-merge, but main has no branch protection and auto-merge is disabled; that is an owner decision."],"evidence":["Product commit 5344eaf9359551efa0f980220d06eb60002840c0 on task/SOS-0001-helper-adoption, based on main 151c819e3457ae41fa1810b5060d0101f91bc12a.","PCM 0b3be9c: continuity preflight --root . -> MODE: TARGET_VALID; diff -r schemas/v1 against the pinned helper -> identical.","CGM f85e88b: validate_content_system.py --adapter .content-system --project-root . -> INVALID with one error: asset-manifest.json must contain at least one asset (no reviewed Study OS visual exists; imagery deferred until R0).","Local CI-equivalent on Python 3.13: dependency lock, contract inventory, curriculum policy, schema render check, compileall, validate_repo.py, engineering baseline, ruff, pyright (0 errors), wheel smoke pass; unittest 350 tests OK (342 before + 8 new); branch coverage 83% (gate 70%).","An earlier unpublished attempt that also edited .github/workflows/ci.yml was rejected by GitHub (token lacks workflow scope); nothing from it was pushed and the workflow edit was removed."],"next_action":"Review the PR for #78; after merge and confirmed checks, mark SOS-0001 completed and clear the continuity:current active task in docs/HANDOFF.md.","protocol_version":"0.1.0-draft","schema":"project-continuity.checkpoint.v1","task_id":"SOS-0001","timestamp":"2026-09-24T20:50:25Z"} -->
<!-- continuity:checkpoint-operation {"payload_sha256":"eb3a491d4b464896d45c8296b7e45fde4584bdead58f9f26229d3c6aac8eeec1","request_id":"sos-0001-cp2-20260924","schema":"project-continuity.checkpoint-operation.v1","task_id":"SOS-0001"} -->

Completed:
- Adopted PCM via the mature-repository overlay: .continuity/config.json (prefix SOS, GitHub issue authority, managed-worktrees), exact schemas/v1 copy, project marker in docs/PROJECT_CHARTER.md, current marker in docs/HANDOFF.md, tasks/ with this issue-backed task.
- Pinned CGM 0.4.0 at f85e88bc00362c53061d95ac7811bd9c6ada8e32 as a .content-system adapter with project-brief v2 claims pinned to Study OS 151c819.
- Recorded ownership rules in AGENTS.md, helper pins in PROJECT_MANIFEST.yaml (0.2.4), decision D015, and tests/test_helper_adoption.py.

Evidence:
- Product commit 5344eaf9359551efa0f980220d06eb60002840c0 on task/SOS-0001-helper-adoption, based on main 151c819e3457ae41fa1810b5060d0101f91bc12a.
- PCM 0b3be9c: continuity preflight --root . -> MODE: TARGET_VALID; diff -r schemas/v1 against the pinned helper -> identical.
- CGM f85e88b: validate_content_system.py --adapter .content-system --project-root . -> INVALID with one error: asset-manifest.json must contain at least one asset (no reviewed Study OS visual exists; imagery deferred until R0).
- Local CI-equivalent on Python 3.13: dependency lock, contract inventory, curriculum policy, schema render check, compileall, validate_repo.py, engineering baseline, ruff, pyright (0 errors), wheel smoke pass; unittest 350 tests OK (342 before + 8 new); branch coverage 83% (gate 70%).
- An earlier unpublished attempt that also edited .github/workflows/ci.yml was rejected by GitHub (token lacks workflow scope); nothing from it was pushed and the workflow edit was removed.

Decisions:
- Canonical PROJECT is docs/PROJECT_CHARTER.md and CURRENT is docs/HANDOFF.md because the YAML manifest cannot carry the line marker; PROJECT_MANIFEST.yaml remains the machine-readable status source.
- Do not fabricate a visual asset to satisfy the CGM validator; record the gap instead.
- Do not change repository settings: PCM expects required CI plus auto-merge, but main has no branch protection and auto-merge is disabled; that is an owner decision.

Changed:
- .continuity/config.json
- schemas/v1/**
- tasks/TASK-SOS-0001-helper-adoption.md
- .content-system/**
- AGENTS.md
- PROJECT_MANIFEST.yaml
- docs/PROJECT_CHARTER.md
- docs/HANDOFF.md
- docs/DECISIONS.md
- .gitignore
- tests/test_helper_adoption.py

Blocked/uncertain:
- Pinned PCM preflight is not yet a CI step: adding it to .github/workflows/ci.yml needs a push with the workflow scope (snippet in the PR description).
- CGM adapter validation stays incomplete until the owner approves a first reviewed Study OS visual or an asset exemption in CGM.
- Required CI and auto-merge are not configured on main.

Next:
- Review the PR for #78; after merge and confirmed checks, mark SOS-0001 completed and clear the continuity:current active task in docs/HANDOFF.md.

## Closeout (2026-09-24, Grok Bot executor for Pukujan)

Owner-authorized closeout. Not a `continuity checkpoint` run, because that command only records checkpoints for active tasks.

- Added the pinned PCM preflight step to `.github/workflows/ci.yml` (`ec2cd66`). CI run [36059729613](https://github.com/Pukujan/Study-os/actions/runs/36059729613): `Validate research harness` passed (step output `MODE: TARGET_VALID`), and `Python 3.11 compatibility` passed.
- Repository settings: auto-merge enabled. `main` protection requires `Validate research harness` and `Python 3.11 compatibility` with strict up-to-date branches, no required reviews, and admins not enforced.
- Status set to completed. The `continuity:current` active task is cleared in `docs/HANDOFF.md`.
- Still open: the CGM asset gap (owner decision; see PR #79 known gaps). The merge SHA and #78 closure are recorded on #78, not here (receipt-only transitions).

## Handoff

Read `docs/PROJECT_CHARTER.md` → `docs/HANDOFF.md` → this task → `AGENTS.md` "Helper modules and project ownership". Checkpoint before stopping.
