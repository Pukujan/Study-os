# Dual-Luna raw transcript run

Status: **current transcript-generation path for PR #77**

The immediate goal is to collect a large, realistic learner-visible transcript before judging or changing tutoring behavior.

## Experiment

Two independent Luna roles participate:

```text
local Luna — student role
        ↓ one realistic learner message
local Luna — teacher role through the normal Study OS path
        ↓ final learner-visible Study OS response
raw transcript recorder
```

The student Luna is guided to behave like a realistic beginner: ask focused clarification questions, make plausible mistakes, attempt recovery, and react to what the teacher just said. It is not given the dataset's expected teaching output, stage, forbidden terms, required terms, or grading rubric.

The teacher Luna must use the real Study OS learner-facing path. The transcript runner does not contain a substitute tutor and does not authorize bypassing Study OS.

## Scale

The current dataset contains 14 DSA scenarios. The default run uses 15 learner/teacher exchanges per scenario:

- 14 problems;
- 210 learner messages;
- 210 teacher responses;
- 420 visible messages total.

That exceeds the requested 10-problem minimum while producing 210 back-and-forth exchanges.

## What the runner does not do

`tools/run_dual_luna_transcript.py` performs **no grading, scoring, pass/fail decision, pedagogical comparison, or automatic repair**. The primary artifacts are the complete raw transcript in JSONL and readable Markdown.

After the transcript exists, it should be brought back for human/model review against the existing calibration dataset and historical teaching examples. Decisions about prompt changes, schema-driven generation, decomposition, canonical assets, or controller behavior should come from that observed transcript rather than from assumptions made before the run.

## Runtime boundary

The orchestration layer is deliberately runtime-agnostic. It requires two JSONL commands:

```bash
python tools/run_dual_luna_transcript.py \
  --student-cmd "<local Luna student adapter>" \
  --teacher-cmd "<local Luna teacher / Study OS adapter>"
```

No OpenCode installation or `luna` OpenCode agent is assumed.

Each command is a long-running process. It reads one JSON object per stdin line and writes one JSON object per stdout line.

### Student actor

Input type: `dual_luna_student_turn`

Important fields:

- `scenario_id`
- `title`
- `problem`
- `turn_index`
- `learner_signal`
- `instruction`
- recent `conversation`

The student returns one of:

```json
{"student_message": "..."}
```

or a generic:

```json
{"message": "..."}
```

The student does not receive dataset `expected`, stage, variable-preservation rubric, forbidden terms, or other answer-key fields.

### Teacher actor

Input type: `dual_luna_teacher_turn`

Important fields:

- `scenario_id`
- `title`
- `problem`
- `turn_index`
- `learner_message`
- `instruction`
- recent `conversation`

The teacher returns the final learner-visible Study OS response as one of:

```json
{"teacher_message": "..."}
```

```json
{"assistant_message": "..."}
```

or:

```json
{"message": "..."}
```

The teacher actor is responsible for actually invoking the normal Study OS product path. The orchestration runner does not emulate Study OS.

## Outputs

Defaults:

```text
artifacts/dual-luna-dsa-transcript.jsonl
artifacts/dual-luna-dsa-transcript.md
```

Every JSONL record contains only transcript/provenance fields:

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

## Development-only short run

A small wiring test can be run without satisfying the 10-problem / 210-exchange floor:

```bash
python tools/run_dual_luna_transcript.py \
  --student-cmd "<student adapter>" \
  --teacher-cmd "<teacher adapter>" \
  --scenario two-sum-dictionary \
  --turns-per-problem 3 \
  --allow-short-run
```

A real evidence run should omit `--allow-short-run`.
