# Model tutoring experiment notebook

This directory is the canonical durable record of **model-tutoring hypotheses, attempts, outcomes, and next experiments**.

A fresh agent or human working on decomposition/tutoring quality should read in this order:

1. `manifest.json` — machine-readable experiment registry and current active proposal;
2. `HISTORY.md` — concise human history of prior approaches and their actual status;
3. the active proposal under `proposals/`;
4. linked calibration evidence via `docs/CALIBRATION_INDEX.md`;
5. linked Issue #63 / PR #77 evidence when implementation detail is required.

## Why this exists

Study OS has already tried multiple tutoring/decomposition strategies. Their evidence is spread across sessions, Issue #63 comments, PRs, prompt versions, qualification artifacts, and handoffs. Fresh sessions can otherwise repeat old ideas or misremember an `insufficient` approach as either a complete failure or a proven solution.

This notebook preserves the experimental sequence without turning `docs/HANDOFF.md` into history.

## Recording rule

Every material experiment should have a stable ID and record:

- question/hypothesis;
- exact inputs and reference artifacts;
- teacher/student/model roles;
- frozen variables and known confounds;
- runner/tool version;
- outputs produced;
- human review surface;
- acceptance condition;
- result/status;
- links to evidence;
- what changes for the next iteration.

Never overwrite a completed experiment record to make a later result look cleaner. Add a new experiment/iteration and link it to its predecessor.

## Current active proposal

`MT-E001` — extract a durable calibration artifact from the learner-calibrated Sliding Window trajectory, then test transfer in a **fresh isolated Sol session** by decomposing and teaching **Two Sum** to a frozen synthetic student. The run should continue until completion or an anti-loop ceiling and emit a self-contained HTML review artifact with the full rendered conversation, ASCII diagrams/charts, per-exchange review controls, and exportable structured annotations.

See:

`proposals/MT-E001-sol-calibration-transfer-two-sum.md`
