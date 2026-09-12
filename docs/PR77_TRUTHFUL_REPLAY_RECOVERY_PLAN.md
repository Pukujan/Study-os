# PR #77 Truthful Replay Recovery Plan

Status: **SUPERSEDED for immediate execution by the user-directed dual-Luna raw transcript experiment**

Last updated: 2026-09-12

PR: #77 — `codex/dsa-conversation-replay-harness`

The previous recovery plan focused on making a stateful replay/judging lane truthful. The user has now clarified that the next required artifact is **not a judge report**. It is the complete raw transcript from two Luna roles:

```text
local Luna acting as a realistic student
        ↓
local Luna acting as the teacher through the real Study OS learner-facing path
        ↓
raw transcript only
```

The current execution authority is:

`docs/DUAL_LUNA_RAW_TRANSCRIPT.md`

Do not continue the older judge-first sequencing until the 10+ problem / 210+ exchange raw transcript has been produced and reviewed.

The raw transcript must be generated without leaking corpus expected-output assertions, stage labels, forbidden terms, or grading rubrics to either Luna. The existing corpus may provide problem statements and coarse learner-behavior signals only.

After the transcript exists, compare the observed Study OS teaching behavior with the calibration dataset and historical examples. Use those observed differences to choose the next implementation work: prompt changes, schema-driven model generation, problem decomposition, canonical teaching assets, controller behavior, or other bounded fixes.

Do not assume OpenCode is the user's Luna runtime. The earlier OpenCode adapter is experimental branch history, not verified product infrastructure.
