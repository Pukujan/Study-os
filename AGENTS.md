# AGENTS.md — Study OS Agent Contract

Study OS is currently a **research-first DSA learning harness**, not a general learning product.

Read these files before making substantive changes:

1. `PROJECT_MANIFEST.yaml`
2. `docs/PROJECT_BOUNDARY.md`
3. `docs/RESEARCH_FOUNDATIONS.md`
4. `docs/FAILURE_MODES.md`
5. `docs/RESEARCH_PLAN.md`
6. `docs/FOSSIL_INTEGRATION.md`
7. `docs/HANDOFF.md`
8. the nearest nested `AGENTS.md`, if present

## Non-negotiable project invariants

- Canonical raw learning evidence is immutable after capture.
- Raw/private transcripts do not belong in the public Git repository.
- Keep `observed`, `self_reported`, and `derived` evidence distinct.
- A learner saying “I understand” is not mastery evidence.
- Derived learner-state claims require provenance and uncertainty.
- Subject-specific observations do not automatically become universal lesson/domain claims.
- FOSSIL is an optional promotion/export layer; Study OS canonical learning data must remain usable without FOSSIL.
- Authoritative DSA state/visualization should be deterministic and testable; generative media is not canonical algorithm state.
- Do not build around fixed “learning styles.” Representations are selected based on task, state, and measured outcome.
- Do not expand beyond the current research gate merely because a feature is technically easy to add.

## Current product/research scope

- learner: `subject-001`
- domain: DSA
- language: Python
- first concept family: Sliding Window
- status: pre-build experiment design / Research Gate R0

See `PROJECT_MANIFEST.yaml` for machine-readable state.

## Pet / mascot animation (A22a)

In-app pet uses **slow JS held-pose spritesheets** (idle + cute ball), Japanese limited 2D, low fps — not CSS keyframe jitter and not Live2D. See [`docs/ops/A22A_HELD_POSE_PET.md`](docs/ops/A22A_HELD_POSE_PET.md). A22b Live2D is a separate comparison slice.

## Plain-human lesson copy

Learner-visible teach / explain-again / worked-example / pack-decomposition markdown goes through a mandatory post-gen rewrite (`src/study_os/web/player/human_rewrite.py`). See [`docs/ops/PLAIN_HUMAN_REWRITE.md`](docs/ops/PLAIN_HUMAN_REWRITE.md). Do not ship walls of AI-blog prose on those surfaces.

## Multi-agent authority

For cross-agent task claims and verdicts, follow [`docs/AUTHORITY.md`](docs/AUTHORITY.md). `grok-bot@study-os` is the sole arbiter; Claude Code + InferHub sessions are claimable workers and must not self-arbitrate or merge to `main`.

For the ACS multi-agent **hotloader** install surface (join-order roles, boss lease, claim queue, watchdog), use the git submodule at `third_party/agent-custom-setup` and start from [`docs/ops/ACS_HOTLOAD.md`](docs/ops/ACS_HOTLOAD.md) → pack [`HOTLOAD.md`](third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/HOTLOAD.md). ACS includes the full PCM/CGM/OIO coordination install; it does not replace Study OS authority. The initial ACS boss lease is vacant, and agent role seeds do not grant verdict or merge authority.

## Agent change protocol

For every substantive task:

1. Read the manifest and handoff.
2. Classify the requested change as one or more of:
   - research;
   - schema/data;
   - ingest;
   - lesson/representation;
   - evaluation;
   - infrastructure;
   - FOSSIL export;
   - product/UI.
3. Check the requested work against project boundaries and research gates.
4. Preserve raw evidence and existing semantic versions.
5. Add/update tests for deterministic behavior.
6. If requirements, scope, gates, canonical paths, schemas, or active risks changed, update:
   - `PROJECT_MANIFEST.yaml`
   - `docs/HANDOFF.md`
7. If an architectural/research decision changed, record it in `docs/DECISIONS.md` or a dedicated decision record.
8. Run repository validation/CI-equivalent checks before declaring completion.
9. Report exactly what remains unresolved.

## Helper modules and project ownership

**This repository is the authoritative owner of Study OS.** Its project facts, scope, gates, evidence semantics, task state, and human-facing claims live here (`AGENTS.md`, `PROJECT_MANIFEST.yaml`, `docs/`, `tasks/`, `.continuity/`, `.content-system/`) and in this repository's GitHub issues, PRs, and merged history. Helper repositories supply reusable method only, at pinned revisions:

| Helper | Role here | Pin (never read moving `main` during work) | Adoption shape |
| --- | --- | --- | --- |
| [`Pukujan/project-continuity-modules`](https://github.com/Pukujan/project-continuity-modules) (PCM) | continuity protocol, validator, checkpoints | CLI `0.7.0`, protocol `0.1.0-draft`, commit `776b468db56cbbe3e251b2583d41f1f0caebd9ba` | mature-repository overlay ([`docs/TARGET_ADOPTION.md`](https://github.com/Pukujan/project-continuity-modules/blob/776b468db56cbbe3e251b2583d41f1f0caebd9ba/docs/TARGET_ADOPTION.md)) |
| [`Pukujan/content-generation-modules`](https://github.com/Pukujan/content-generation-modules) (CGM) | README/brand/visual/image method and adapter validator | `0.5.12`, commit `78385ff2ba31051128208ddc7f08dc5de0f0b570` (see `.content-system/system-version.json`) | target adapter in `.content-system/` |
| [`Pukujan/agent-custom-setup`](https://github.com/Pukujan/agent-custom-setup) (ACS) | multi-agent hotloader pack (roles, boss lease, claim queue, watchdog) | commit `264117398e7754d7e91076481cd664b5e197c1d4` (certified ACS release) | git submodule at `third_party/agent-custom-setup`; load [`HOTLOAD.md`](third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/HOTLOAD.md) — see [`docs/ops/ACS_HOTLOAD.md`](docs/ops/ACS_HOTLOAD.md) |

Rules:

- Helpers never own Study OS state. Do not write Study OS PROJECT/CURRENT/TASK state, learner data, or product claims into a helper repository, and do not use a helper's own `CURRENT`/`TASK` files as Study OS state.
- PCM canonical paths (declared in `.continuity/config.json`): PROJECT = `docs/PROJECT_CHARTER.md`, CURRENT = `docs/HANDOFF.md`, TASKS = `tasks/`. The `continuity:*` marker lines only declare those roles; they do not change the documents' existing meaning. `PROJECT_MANIFEST.yaml` stays the machine-readable status/guardrail source.
- `schemas/v1/**` is an exact copy of PCM's protocol schemas at the pinned commit. Study OS domain schemas stay in `schemas/*.schema.json`. Do not edit `schemas/v1/` except when deliberately moving the PCM pin.
- Before relying on continuity state, run the pinned PCM validator against this root and require `MODE: TARGET_VALID`:

  ```bash
  git clone https://github.com/Pukujan/project-continuity-modules /tmp/pcm && git -C /tmp/pcm checkout 776b468db56cbbe3e251b2583d41f1f0caebd9ba
  PYTHONPATH=/tmp/pcm/src python -m continuity preflight --root .
  ```

- GitHub issues own task scope, acceptance, priority, owner, dependencies, and lifecycle; merged `main` owns accepted code/docs; PR/check records own delivery facts. `tasks/TASK-SOS-*.md` and the `continuity:current` marker are versioned projections of that state (PCM [SPEC section 8](https://github.com/Pukujan/project-continuity-modules/blob/776b468db56cbbe3e251b2583d41f1f0caebd9ba/SPEC.md#8-authority)). Every PCM task needs an owning issue (`issue_url`); every progress update names the leaf issue, parent (or "none"), and dependencies (or "none").
- Work one task per branch (`task/SOS-XXXX-slug`), one primary writer per task. Commit product changes first, then `continuity checkpoint` (it commits and pushes the task branch), then open/update the PR and post a receipt on the leaf issue with the pushed SHA. Never push to `main` or force-push.
- Human-facing deliverables (README, product docs, image briefs, demos) follow the pinned CGM contract and `.content-system/` adapter. Claims in `.content-system/project-brief.json` must cite exact Study OS revisions and state what each source supports and leaves unproven. Generated imagery remains deferred until Research Gate R0 (see "Explicitly deferred").
- Private repositories (for example `Pukujan/private-study-log`) are never copied, quoted, or summarized into this public repository, its issues/PRs, or helper repositories.
- ACS hotloader is a **git submodule** only (`third_party/agent-custom-setup`). Do not vendor-copy the pack. Init with `git submodule update --init --recursive third_party/agent-custom-setup`. Re-pin only via an issue-backed PR when the certified agent-stack-train release changes; use the real ACS installer and its full validation gates.
- Moving a helper pin is its own issue-backed change: update the pin here, in `.continuity/config.json`/`schemas/v1/` or `.content-system/system-version.json`, run both validators, and record the result.


### CGM always-on writing rule (0.5.12+)

Paste target for agent boot. Exact text from the pinned helper `docs/writing-routing.json` → `acs_prompt_inject.system_block`:

```text
CGM ALWAYS-ON WRITING RULE (every adopter that pins this helper)

Before you write ANY human-facing output — including HTML reports, compare HTML/UIs, appendable HTML, PR/issue/commit prose, docs, posts, papers, or other readable artifacts — you MUST load and apply modules/human-sounding-writing/SKILL.md (hsw).

This rule is always on. Opt-in is forbidden. Do not wait for a per-task, per-report, or per-HTML flag.

Exceptions (only these):
- README.md / product entry pages → load modules/writing-direction/SKILL.md instead
- Generated artifact filenames / asset-manifest paths / media basenames / filename legends → load modules/human-output-naming/SKILL.md (hon) for basenames; visible prose inside HTML still uses hsw

HTML reports, compare HTML, and compare UIs have NO skip path. An exception reason is not allowed for those surfaces.

If you cannot load the skill file from the pinned CGM checkout, stop and report that — do not draft jargon-heavy or tool-dump HTML instead.

Filenames: use scripts/human_filename (speakable basenames; optional safe_twin) and keep a per-feature legend. Hash may stay a separate manifest field.
```

## Handoff protocol

`docs/HANDOFF.md` is a living operational snapshot for the next agent. Keep it concise and current. It must include:

- current phase/gate;
- last meaningful changes;
- active experiment;
- unresolved decisions;
- next recommended tasks;
- known hazards/data-boundary reminders.

Do not turn HANDOFF into history. Git and issues provide history.

## Manifest update protocol

`PROJECT_MANIFEST.yaml` is the machine-readable source for project status and guardrails.

Update it when any of these change:

- current research gate;
- active learner/domain/concept;
- schema versions;
- canonical storage paths;
- required CI checks;
- FOSSIL integration policy;
- build/deployment status;
- major open risks;
- next research milestone.

Agents may update the manifest, but must never silently relax a project invariant. A relaxation requires an explicit decision record and should be surfaced to the user.

## Data handling

This repository is public.

- Full raw transcripts: local/private evidence store by default.
- Public repo: hashes, manifests, redacted fixtures, schemas, reviewed/curated derived records.
- Do not commit secrets, account identifiers, private conversation exports, or hidden evaluation answers.
- Hidden transfer/eval material should be separated from tutor-visible content when possible.

## Research integrity

Prefer behavioral evidence over impression:

1. deterministic correctness/tests;
2. unaided behavior;
3. transfer;
4. delayed retention;
5. self-report;
6. model-derived interpretation.

Self-report is valuable but is not automatically causal evidence.

When comparing interventions, record confounds and avoid implying causality when multiple variables changed.

## DSA pedagogy contract

Teach and measure translation between:

`problem -> recognition -> mental model -> state -> invariant -> procedure -> pseudocode -> code -> debugging -> transfer`

Prefer semantic operations before syntax memorization.

Initial learning operations include:

- expand;
- decompose;
- trace;
- predict;
- explain;
- contrast;
- abstract;
- specialize;
- reconstruct;
- debug;
- translate;
- fade;
- transfer.

## Build/test expectations

Until a package layout is formalized, the minimum checks are defined in `.github/workflows/ci.yml` and `tools/validate_repo.py`.

Expected local checks:

```bash
python -m compileall tools tests
python tools/validate_repo.py
python -m unittest discover -s tests -v
```

`tests/test_helper_adoption.py` (part of the unittest suite) checks the helper pins, PCM canonical markers, and CGM adapter shape offline. The full PCM/CGM validators require the pinned helper checkouts; see "Helper modules and project ownership".

If dependencies are later added, update this file and CI together.

## Pull request expectations

A substantive PR should state:

- research/product question addressed;
- data/schema impact;
- evidence class affected;
- tests performed;
- research gate impact;
- known limitations;
- whether manifest/handoff changed.

## Human feedback calibration (mandatory before inventing UX)

Before inventing or changing learner-visible UX, **append then read** Alex’s critiques:

- Pack: [`content/human-feedback/`](content/human-feedback/) (`feedback.jsonl` + `assets/`)
- Ops: [`docs/ops/HUMAN_FEEDBACK.md`](docs/ops/HUMAN_FEEDBACK.md) (Refs [#164](https://github.com/Pukujan/Study-os/issues/164))
- **Reuse** Postgres `ux.feedback` and `ux.decomposer_review` for live in-app / decomposer ratings; reuse `sessions/` for verbatim calibration chats. **Do not** create a parallel feedback database.

## Frontend QA mandate (mandatory)

**Ultrafast-first (local/scout), then Playwright.** Never claim a frontend change works — or open/merge a UI PR as “FE done” — without a **local Ultrafast pass**, then Playwright.

Full policy: [`docs/AGENT_FRONTEND_QA.md`](docs/AGENT_FRONTEND_QA.md).

Non-negotiable summary:

1. **Ultrafast FIRST** — local scout against live `https://study.design-bakery.com` or the PR preview (Teresa-Pujan: `tools/ux-defect/Run-UltrafastScout.ps1`; Linux/box: `./tools/frontend_qa/run_ultrafast_scout.sh`).
2. **Then Playwright** UX / vision (local and/or CI).
3. **CI stays Playwright + vision only.** Ultrafast is **not** a required GitHub Actions job — do not add an `ultrafast-ux` (or similar) Actions workflow.
4. Any **P0/P1** fail → claim fails **regardless of confidence**. Fix or file and block; never re-label pass.
5. **Low confidence** → manually re-check why; do not skip. Record confidence; it does **not** waive P0/P1.
6. **Ultrafast is reliable.** Do not call it flaky. OpenRouter Decisions misconfig / missing `OPENROUTER_API_KEY` / HTTP 400 from the Decisions API is an **env/config problem**, not an Ultrafast flake.
7. **No Jev / OpenRouter Decisions on product code.** Ultrafast is a QA harness only.

Runners (order matters):

```bash
# 1) Local Ultrafast scout (REQUIRED for FE claims — not CI)
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com   # or PR preview URL
python tools/gate_ux_defect_report.py artifacts/ux-defect-ultrafast/<stamp>/summary.json

# 2) Playwright UX + vision
./tools/frontend_qa/run_playwright_ux.sh
```

Windows / Teresa-Pujan (preferred host for Ultrafast):

```powershell
powershell -File tools/ux-defect/Run-UltrafastScout.ps1   # uses D:\claude\jev-ultrafast or $env:JEV_ULTRAFAST_ROOT
powershell -File tools/ux-defect/Run-PlaywrightDefectPass.ps1
```

See `docs/UX_DEFECT_LOCAL_AND_CI.md` (local Ultrafast = agent FE claim gate; CI merge gate = Playwright + vision only).

Ultrafast lives at [`Pukujan/jev-ultrafast`](https://github.com/Pukujan/jev-ultrafast) (Teresa-Pujan default `D:\claude\jev-ultrafast`). Playwright specs: `web/e2e/` (incl. `ux-defect-controls.spec.ts`). Required CI job for UI: `playwright` in `.github/workflows/ci.yml` — **not** Ultrafast.


## Explicitly deferred

Until Research Gate R0 passes, do not prioritize:

- production UI;
- CD/deployment;
- full DSA curriculum;
- video/image generation pipelines;
- generalized learner recommendation models;
- universal learning claims.

## Teach visuals

- Big O step-1 diagrams: [`docs/ops/TEACH_VISUAL_V1.md`](docs/ops/TEACH_VISUAL_V1.md) (`STUDY_OS_TEACH_VISUAL_V1=0` restores legacy table).

<!-- oio:issue-log-guidance:start -->
Before filing an observational or operational issue log, read `.oio/ontology/ISSUE_LOG_ONTOLOGY.md`, `.oio/ontology/project.json`, and `.oio/ontology/AGENT_GUIDE.md`. Confirm the exact destination and filing action are authorized. On OIO, ACS, CGM, and PCM, do not submit an issue or write files without explicit human direction for that destination and action. A proposal can remain a local draft until directed. Never treat adoption as permission to write to an adopter or sibling repository.
<!-- oio:issue-log-guidance:end -->
