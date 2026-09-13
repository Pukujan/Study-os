# Dual-Luna raw transcript run

Status: **current transcript-generation path for PR #77**

The immediate goal is to collect a large, realistic learner-visible transcript before judging or changing tutoring behavior.

## Experiment

```text
local Luna — realistic student
        ↓ one learner message
local Luna — teacher through Study OS MCP
        ↓ final learner-visible Study OS response
raw transcript recorder
```

The student asks questions, makes plausible mistakes, attempts recovery, and reacts to the teacher. It receives no expected teaching output, stage, forbidden terms, required terms, or grading rubric.

The teacher must use the real Study OS path. Free-form teacher answers that did not complete a Study OS MCP call are rejected by the local harness and are not recorded.

## Scale

- 14 DSA problems;
- 15 learner/teacher exchanges per problem;
- 210 learner messages;
- 210 teacher responses;
- 420 visible messages total.

## Preferred local execution

```bash
python tools/run_dual_luna_local_codex.py
```

This is the preferred path because it removes the test-infrastructure friction that came from hosted child tasks. It automatically checks the local runtime, registers this checkout's Study OS stdio MCP with Codex under a test-only name, runs two local resumable Codex/Luna roles, suppresses local approval/sandbox pauses for this harness, verifies teacher Study OS tool use, checkpoints every completed exchange, and resumes interrupted transcripts.

See `docs/DUAL_LUNA_LOCAL_EXECUTION_HANDOFF.md` for the exact local behavior.

`tools/run_dual_luna_transcript.py` remains the runtime-agnostic orchestration core and fallback actor interface; it is not the normal path the user should have to wire manually.

No OpenCode installation or OpenCode `luna` agent is assumed.

## Evidence boundary

Generation performs **no pedagogical grading, scoring, pass/fail decision, comparison, or automatic repair**. The purpose is to observe what Study OS actually shows a realistic learner.

After the raw transcript exists, bring it back for review against the existing calibration dataset and historical teaching examples. Only then decide whether the observed failures require prompt changes, schema-constrained generation, decomposition, canonical assets, controller changes, or something else.

## Dataset boundary

The existing DSA corpus supplies only:

- scenario id/title;
- problem statement;
- a coarse learner-behavior signal such as `clarification`, `wrong_or_uncertain`, or `recovery_or_check`.

Neither Luna receives the corpus `expected` assertions, stage labels, variable-preservation rubric, forbidden terms, required terms, or answer key.

Every turn includes the full conversation for that current problem. This makes a local Luna session restart recoverable without changing the logical learner/teacher conversation.

## Outputs

```text
artifacts/dual-luna-dsa-transcript.jsonl
artifacts/dual-luna-dsa-transcript.md
```

Each JSONL record contains only raw transcript/provenance fields:

```text
scenario_id
title
problem
turn_index
learner_signal
learner_message
teacher_message
```

There are intentionally no `violations`, `score`, `passed`, `expected`, or verdict fields.

The files are updated after every completed exchange. Re-running the preferred local command continues from the existing JSONL artifact unless `--fresh` is explicitly supplied.

## Development-only smoke

```bash
python tools/run_dual_luna_local_codex.py \
  --fresh \
  --scenario two-sum-dictionary \
  --turns-per-problem 3 \
  --allow-short-run
```

The real evidence run is simply:

```bash
python tools/run_dual_luna_local_codex.py
```
