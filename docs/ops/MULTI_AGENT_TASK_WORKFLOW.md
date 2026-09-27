# Multi-agent task workflow port (from jev-classifier → Study-os)

**Status:** design note (local Teresa workspace). Not yet accepted product policy.
**Date:** 2026-09-27 (America/New_York)
**Owner authority target:** Study-os Grok Bot (arbiter for `Pukujan/Study-os`)
**Workers:** Claude Code sessions with InferHub keys (claim + implement only)
**Source epic for first queue feed:** [#126](https://github.com/Pukujan/Study-os/issues/126) feedback/ops comments (A12…A24 slices)
**Do not:** mass-copy private notes, secrets, or learner transcripts into this tree.

---

## 1. Where the jev-classifier workflow lives

### Canonical copies inspected

| Location | Role |
| --- | --- |
| GitHub `Pukujan/jev-classifier` | Authority for that project’s coordination protocol |
| `D:\claude\jev-classifier` (Teresa, machine `a68d3478-…`) | Live checkout + worktrees; matches protocol docs |
| Box `/workspace/jev-classifier` | Readable mirror used for this survey |

### Key files (paths relative to jev-classifier root)

| Path | Purpose |
| --- | --- |
| `docs/AUTHORITY.md` | Sole arbiter policy; GitHub issues/PRs as canonical work authority |
| `docs/AGENT_COORD.md` | Local SQLite CoordStore = execution aid only (not cross-device lock) |
| `docs/AGENT_PROPOSALS.md` | Machine grammar: `coord:proposal` / `coord:verdict` / `coord:claim` / `coord:receipt` / `coord:message` |
| `AGENTS.md` | Agent operating rules + pointer to coordination layer v2 |
| `tasks/README.md` + `tasks/TASK-JEV-*.md` | PCM task projections (`project-continuity.task.v1`) |
| `schemas/v1/task.schema.json` | Task metadata schema (PCM copy) |
| `.continuity/config.json` | `task_prefix: JEV`, tasks dir, GitHub tracker |
| `src/jev_classifier/coord/store.py` | Local claim/checkpoint/send_log SQLite |
| `src/jev_classifier/coord/records.py` | Parser/folder; `AUTHORITATIVE_AGENTS` roster |
| `scripts/coord_board.py` | Gate CLI: `--issue-open N --agent you` → exit 0 go / 3 blocked |
| `scripts/ops_sync.py` | Regenerates committed board from live GitHub comments |
| `ops/ledger/COORD.md` | Committed **projection** of live claims / proposals / receipts |
| `ops/ledger/ISSUE_LOG.md`, `DISCREPANCIES.md`, `issues/*.json` | Ops projections |
| `.github/workflows/ci.yml` | Offline pytest + `coord_board` smoke on fixture comments |
| `docs/CURRENT.md` | Human board projection (`continuity:current`) |

Related (not Study-os product): `D:\claude\multi-agent-modules` has a **proposed** intake schema (`proposals/task-intake.schema.json`, `mam.task-intake.v1`) for cold-start/handoff — useful later, **not** required for the first Study-os claim queue.

---

## 2. Architecture summary (jev-classifier)

### Authority stack

1. **GitHub issues/PRs** — sole authority for work items, ownership, decisions, delivery.
2. **`docs/CURRENT.md` + `tasks/TASK-*.md`** — human/machine continuity projections (PCM).
3. **`ops/ledger/*`** — regenerated readable board; never arbiter.
4. **`.coord/agents.db` (gitignored)** — per-device collision aid; rebuildable; GitHub wins on conflict.

### How work moves

```text
Open leaf issue (name reserved branch feat/<slug>-<n>)
        │
        ▼
Worker posts coord:proposal (optional if uncontested)
        │
        ▼
Arbiter posts coord:verdict (accepted|rejected|…)  ← only roster roles apply
        │
        ▼
Worker: push marker commit on reserved branch (cross-device mutex)
        + post coord:claim (issue, agent, branch, sha, state=active)
        │
        ▼
Gate: python scripts/coord_board.py --issue-open N --agent <role@device>
        FREE | CLAIMED-BY-YOU → implement; else stop
        │
        ▼
Small PR from claimed branch → CI → merge/close auto-releases claim
        │
        ▼
coord:receipt (append-only run evidence + per-field provenance)
```

### Formats

| Layer | Format |
| --- | --- |
| Work lock | HTML comment markers on issue comments + reserved git ref |
| Task resume card | Markdown `tasks/TASK-<PREFIX>-NNNN-*.md` with `<!-- continuity:task {json} -->` |
| Board | Markdown tables in `ops/ledger/COORD.md` |
| Local aid | SQLite tables: ownership, checkpoints, send_log, collision_flags |
| CI | Offline fixture path for `coord_board`; no secrets |

### Agent roles (jev)

- **Authoritative agent** (`claude-code-main` roster role in that repo): sole arbiter of proposals/verdicts.
- **Product/workers**: propose, claim, implement, receipt — never self-arbitrate.
- **Shared GitHub account**: `agent=` / `by=` are evidence, not cryptographic enforcement; session ids use `role@device`.

---

## 3. Study-os port plan

### Goals

- Claude Code workers (InferHub BYOK) can **claim** discrete #126 feedback slices and implement on feature branches.
- **Study-os Grok Bot** remains authoritative owner of `Pukujan/Study-os`: creates/assigns/reviews/verdicts; may also implement when needed.
- No second product owner in PCM/CGM/MAM/helpers. No product UI code in this port.

### Where it lives in Study-os

| Path | What to add (minimal first ship) |
| --- | --- |
| `docs/AUTHORITY.md` | Study-os binding policy: Grok Bot = arbiter; InferHub Claude = worker lane |
| `docs/AGENT_COORD.md` | Short port of claim protocol (GitHub + reserved branch); SQLite optional later |
| `docs/AGENT_PROPOSALS.md` | Marker grammar (copy mechanics, change roster) |
| `AGENTS.md` | Link authority + “gate before product commits” |
| `tasks/TASK-SOS-*.md` | Already present (PCM); use for claimable atomics |
| `schemas/v1/task.schema.json` | Already PCM — keep; do **not** invent parallel task schema for continuity |
| `docs/ops/COORD.md` | Committed board projection (start manual or thin sync script) |
| `docs/ops/MULTI_AGENT_TASK_WORKFLOW.md` | This design note |
| `scripts/coord_board.py` (later) | Port or thin-wrap jev’s gate; offline fixtures under `tests/fixtures/coord/` |
| `.github/workflows/*` | Later: offline gate smoke only (no secrets) |

Prefer **docs + markers + existing `tasks/`** before copying `jev_classifier.coord` Python. Study-os already has PCM continuity; the missing piece is the **cross-device claim mutex + arbiter roster**.

### Role map for Study-os

| Role | Agent id pattern | May do | Must not do |
| --- | --- | --- | --- |
| Arbiter | `grok-bot@study-os` (roster exact/role) | `coord:verdict`, create/assign leaves, accept/reject claims, review PRs, release/supersede | Hand arbiter rights to workers |
| Planner (Astra) | `astra@…` | Research, PDD/SDD/TDD, RED tests, GitHub specs on issues | Ship product code (existing #126 policy) |
| Worker (Claude/InferHub) | `claude-code@teresa-inferhub` etc. | `coord:proposal`, `coord:claim`, implement, PR, `coord:receipt` | Write authoritative verdicts; claim without gate; merge to main without review |
| Continuity helpers | PCM/CGM pins | Method only | Own Study-os state |

### How #126 feedback queue becomes claimable tasks

Today #126 comments are an **ops feedback queue** (A12 arrows, A18 blank-play, A19…A24). Port steps:

1. **Grok Bot** (or owner) turns each durable feedback item into either:
   - a **leaf GitHub issue** (preferred for P0), or
   - a **numbered atomic** on #126 with explicit `branch=` and done-when (acceptable for short slices).
2. Write/update `tasks/TASK-SOS-NNNN-*.md` projection (`status: queued`, `issue_url`, acceptance, allowed files).
3. Post `coord:proposal` (worker or Bot) → Bot `coord:verdict decision=accepted` naming primary writer + branch.
4. Worker reserves `feat/<slug>-126` or leaf issue number, marker-push, `coord:claim`, implements via InferHub, opens PR Refs #126 (or closes leaf).
5. Bot reviews; merge/close releases claim; worker posts `coord:receipt`.

**Queue → task mapping rule:** one claimable task = one reserved branch = one primary writer. Do not let A12 and A18 share a worktree without separate branches (already practiced on Teresa).

### Anti-patterns for Study-os

- Treating Astra or InferHub worker as arbiter.
- Claiming only in chat/local SQLite without reserved branch + `coord:claim`.
- Copying private learner data / absolute secret paths into tasks or receipts.
- Mass-importing jev’s JEV-only classifier rules into Study-os product logic.
- Building a product UI for the task board (out of scope).

---

## 4. Comment outline for Study-os #126

Post as a short design pointer (not a paste of private content):

1. **Title:** `## Design: multi-agent claim queue (jev-classifier port) — Grok Bot arbiter`
2. **Problem:** #126 feedback slices (A12/A18/…) need parallel InferHub workers without colliding or inventing a second owner.
3. **Source:** adopt mechanics from `Pukujan/jev-classifier` (`docs/AUTHORITY.md`, `docs/AGENT_PROPOSALS.md`, reserved-branch + `coord:*` markers); Study-os keeps product authority.
4. **Authority:** Grok Bot = sole arbiter (`coord:verdict`); Claude Code + InferHub = claim/implement/receipt only; Astra stays plan/spec/RED per existing policy.
5. **Queue rule:** each durable feedback item → claimable leaf or atomic with branch + acceptance; first example = **A18 blank-play**.
6. **Pointer:** local design note `docs/ops/MULTI_AGENT_TASK_WORKFLOW.md` (this file) + example schema/task below; PR later to land on `main`.
7. **Next ship:** minimal queue schema fields + one queued A18 task card; no UI.
8. **Non-goals:** no secret paste; no mass private transcript copy; no product task-board UI.

---

## 5. Concrete next ship

### 5.1 Minimal task-queue schema (Study-os claim card)

Reuse PCM `project-continuity.task.v1` for the task file. Add a **thin claim envelope** (issue comment or sidecar JSON) — not a second continuity schema:

```json
{
  "schema": "study-os.claim-queue.v1",
  "task_id": "SOS-00XX",
  "issue_ref": "Pukujan/Study-os#126",
  "atomic": "A18",
  "priority": "P0",
  "status": "queued",
  "arbiter": "grok-bot@study-os",
  "allowed_roles": ["claude-code", "inferhub-worker"],
  "branch": "task/SOS-player-blank-play-2026-09-26",
  "worktree_hint": "D:\\\\claude\\\\_workspace\\\\study-os-A18",
  "model_hint": "cb/deepseek-v4.1-flash",
  "depends_on": [],
  "acceptance": [
    "worked_example public shape renders without whitescreen",
    "ErrorBoundary offers Retry/Go home",
    "browser back / Resume never blank the play root",
    "PR Refs #126; CI green"
  ],
  "out_of_scope": ["product task-board UI", "private transcript paste"]
}
```

Field rules:

- `status`: `queued` | `claimed` | `in_review` | `done` | `cancelled`
- `branch` required before `claimed`
- Only arbiter may move `queued` → cancelled or force-release another agent’s claim
- Workers set `claimed` only together with a live `coord:claim` + successful marker push

### 5.2 Example task — A18 blank-play

See sibling file: [`examples/TASK-SOS-A18-blank-play.example.md`](examples/TASK-SOS-A18-blank-play.example.md).

Public done-when (from #126 ops, non-private):

- Chat/chip “Show a worked example” must not unmount the React root.
- Browser back and Resume must show real content or bounded error UI — never empty lavender shell.
- Fix path: public `worked_example` shape (`md` / safe steps) + ErrorBoundary + session remount hygiene.
- Ship PR Refs #126; do not collide with A12 worktree/branch.

### 5.3 Ship checklist (minimal)

1. Land this design note + example task under `docs/ops/` via PR (Refs #126).
2. Add `docs/AUTHORITY.md` naming `grok-bot` as Study-os arbiter roster role.
3. Bot posts #126 comment using section 4 outline + accepts A18 example as first claimable atomic (if still open / needs follow-up).
4. Later PR: port `coord_board` gate + `ops` ledger sync (copy mechanics from jev, Study-os package path).

---

## 6. Source → Study-os mapping cheat sheet

| jev-classifier | Study-os |
| --- | --- |
| Arbiter `claude-code-main` | Arbiter `grok-bot` |
| Workers various Claude/Codex | InferHub Claude Code workers |
| `task_prefix: JEV` | `task_prefix: SOS` (already) |
| `ops/ledger/COORD.md` | `docs/ops/COORD.md` (start) or `ops/ledger/` if package added |
| JEV-only classifier rules | **Do not port** — Study-os has its own research invariants |
| OpenRouter Decisions API | Irrelevant to claim queue |
