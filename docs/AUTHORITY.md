# Study OS authority and worker coordination

**Status:** repository policy
**Arbiter:** `grok-bot@study-os`
**Repository:** `Pukujan/Study-os`

## Authority

`grok-bot@study-os` is the sole arbiter for Study OS multi-agent work. The arbiter owns the authoritative decision on task intake, scope, acceptance, worker assignment, claim conflicts, verdicts, PR review, and merge/release. GitHub issues, pull requests, reviews, checks, and merged history are the canonical record; local files, chat, and local coordination state are only projections or execution aids.

No worker, helper repository, model, or local checkout may substitute its own decision for the arbiter's verdict or grant itself authority. A worker must stop when a task is not explicitly claimable or when the arbiter has rejected, superseded, or released its claim.

## Claimable worker lane

Claude Code sessions operating through InferHub are claimable workers. They may, when the arbiter has accepted the work:

- propose or clarify a bounded task;
- claim one task on one reserved branch/worktree;
- implement the approved scope, including docs or product changes explicitly allowed by the task;
- open or update a focused PR and report checks;
- post an append-only receipt after review or merge.

Workers must not issue authoritative `coord:verdict` decisions, reassign another worker, merge to `main`, or broaden the accepted scope. A claim is not valid based on chat or a local lock alone: it requires the arbiter-approved task, a reserved branch, and a GitHub-visible claim marker or equivalent receipt.

## Required handoff

Every worker claim should identify the issue or task, worker identity, branch, worktree, commit/marker SHA, allowed files, acceptance criteria, and dependencies. Keep one primary writer per task and do not share a worktree across parallel tasks. PRs should name the task/issue, remain docs-only when the task says docs-only, and include validation performed and known limitations.

For the initial coordination port and the A18 example, see [`docs/ops/MULTI_AGENT_TASK_WORKFLOW.md`](ops/MULTI_AGENT_TASK_WORKFLOW.md) and [`docs/ops/examples/TASK-SOS-A18-blank-play.example.md`](ops/examples/TASK-SOS-A18-blank-play.example.md). This policy does not authorize a product task-board UI or copying private transcripts, secrets, or local credentials into the repository.
