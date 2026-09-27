# ACS multi-agent hotloader (submodule)

**Status:** installed as git submodule (not a vendor copy).  
**Date:** 2026-09-27 (America/New_York)  
**Refs:** [#126](https://github.com/Pukujan/Study-os/issues/126)

## What this is

[Pukujan/agent-custom-setup](https://github.com/Pukujan/agent-custom-setup) (ACS) is checked in at:

| Item | Value |
| --- | --- |
| Submodule path | `third_party/agent-custom-setup` |
| Pin commit | `f9650936fd5fd66be3b0e2cf04e653f0a3cbb7e4` (ACS PR [#12](https://github.com/Pukujan/agent-custom-setup/pull/12) tip; pack not on ACS `main` yet) |
| Hotloader pack | `third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/` |
| Startup guide | [`HOTLOAD.md`](../../third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/HOTLOAD.md) |
| Pack README | [`README.md`](../../third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/README.md) |

ACS does **not** replace PCM or CGM. The hotloader wires PCM + CGM + the coordination runtime (join-order roles, boss lease, claim queue, watchdog, proposals to claim to PR). Study OS remains authoritative for product state; see `AGENTS.md` and `docs/AUTHORITY.md`.

## Init after clone

```bash
git submodule update --init --recursive third_party/agent-custom-setup
# confirm pin (should be f9650936…)
git -C third_party/agent-custom-setup rev-parse HEAD
```

## Load order (agents)

Follow the pack's [HOTLOAD.md](../../third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/HOTLOAD.md):

1. ACS policy / registry inside the submodule (when present on the pin)
2. PCM (Study OS already adopts PCM — continuity only)
3. CGM (Study OS already adopts CGM — titles/UX; pack may name a newer HSW pin for hotload prose)
4. This runtime: `ROLES.md`, `BEHAVIOR.md`, `PROPOSALS.md`, assignment with `boss_failover` + `watchdog`

Study-os arbiter remains `grok-bot@study-os` per `docs/AUTHORITY.md`. Live join/continue order fills hotload roles; tool identity does not.

## Verify pack

From the Study OS root (requires the submodule initialized):

```bash
python third_party/agent-custom-setup/modules/coordination/multi-agent-hotload/v0.1.0/scripts/hotload_check.py
```

Optional: `--assignment path/to/assignment.json` (defaults to the pack example).

## Re-pin

When ACS PR #12 merges to `main`, bump the submodule to the merge commit on ACS `main` in a separate issue-backed PR. Do not track moving `main` during work. Do not copy the pack into `vendor/` — keep the submodule.

## Related

- Multi-agent authority: `docs/AUTHORITY.md`
- Port notes (jev-classifier to Study-os): `docs/ops/MULTI_AGENT_TASK_WORKFLOW.md`
- ACS owning issue for the pack: [agent-custom-setup#11](https://github.com/Pukujan/agent-custom-setup/issues/11)

- Claude Code pasteable worker handoff: [`docs/ops/CLAUDE_CODE_WORKER_HANDOFF.md`](CLAUDE_CODE_WORKER_HANDOFF.md)
