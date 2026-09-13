# Local Luna handoff — run the dual-Luna transcript without hosted child tasks

Status: **immediate local execution task for PR #77**

## Objective

Produce the requested raw transcript and nothing else first:

```text
local Luna student
    ↓
local Luna teacher using Study OS MCP/product path
    ↓
14 DSA problems × 15 exchanges
    ↓
210 learner messages + 210 teacher responses
    ↓
raw JSONL + Markdown transcript
```

Do not grade, repair, redesign tutoring, or compare against the calibration dataset during generation.

## Do not use hosted child Codex tasks

Hosted child threads introduced an unnecessary sandbox/approval boundary and are not required for this experiment. Do not spend time trying to propagate parent approval settings into hosted children.

The preferred local path is now:

```bash
python tools/run_dual_luna_local_codex.py
```

This script starts two independent **local Codex CLI sessions** and resumes each one turn-by-turn with `codex exec resume <thread-id>`. A fresh pair of sessions is used for each DSA problem.

By default the script launches local Codex with:

```text
--dangerously-bypass-approvals-and-sandbox
```

so the local teacher can call the configured Study OS MCP service without pausing for approval. This is intentionally a local test harness choice. To restore the normal Codex sandbox, run with `--keep-codex-sandbox`.

## Why this solves the blocker

We do not need:

- hosted Codex child threads;
- inherited child approval policy;
- a persistent child-task API;
- OpenCode;
- a long-running JSONL Luna daemon.

Codex CLI sessions themselves are persistent. The runner records the `thread_id` from the first `codex exec --json` call and uses `codex exec ... resume <thread-id> -` for later turns.

The runner fails closed if a resume unexpectedly reports a different thread ID, so a missing/stale session cannot silently become a fresh conversation.

## Teacher requirement

The teacher Luna is instructed on every turn to use the configured Study OS MCP/product path and return only the final learner-visible response. It must not answer as a standalone tutor or edit the repository.

If the teacher cannot see/call Study OS MCP from this local Codex process, fix **that local Codex MCP configuration/path only**. Do not reintroduce hosted child tasks as a workaround.

## Student requirement

The student Luna receives the problem, recent conversation, and only the coarse behavioral signal from the corpus (`clarification`, `wrong_or_uncertain`, `recovery_or_check`). It does not receive expected answers, stages, forbidden terms, grading rules, or calibration output.

## First smoke

Before the 210-exchange run, prove wiring with:

```bash
python tools/run_dual_luna_local_codex.py \
  --scenario two-sum-dictionary \
  --turns-per-problem 3 \
  --allow-short-run
```

Expected result: six visible messages in the Markdown artifact, no approval pause, and the teacher responses are produced through Study OS.

Then run the full command with no short-run flags:

```bash
python tools/run_dual_luna_local_codex.py
```

Outputs:

```text
artifacts/dual-luna-dsa-transcript.jsonl
artifacts/dual-luna-dsa-transcript.md
```

## If local Codex resume is not usable

Use this fallback order, without changing the experiment:

1. local Codex app-server with two thread IDs;
2. direct local/model API sessions with two independent conversation histories, with teacher tool access wired to Study OS MCP;
3. the generic `tools/run_dual_luna_transcript.py` actor interface.

Do **not** return to hosted child tasks merely to preserve the previous harness design.

## Stop condition

The immediate task is complete only when the raw 210-exchange transcript exists. Bring that artifact back for analysis before deciding any tutoring architecture changes.
