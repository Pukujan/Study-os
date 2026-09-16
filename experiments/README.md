# Study OS experiments

This directory is the durable notebook for product/research experiments that should survive fresh agents, fresh ChatGPT sessions, and changing implementation approaches.

Use it for **what we tried, what happened, what we learned, and what we are trying next**. It complements, rather than replaces:

- `docs/DECISIONS.md` for accepted architecture/research decisions;
- `docs/HANDOFF.md` for the current operational snapshot;
- GitHub Issues/PRs for chronological discussion and implementation history;
- `docs/CALIBRATION_INDEX.md` + `calibration/manifest.json` for calibration-source discovery;
- raw/session evidence for what actually happened.

Experiment records must distinguish at least these statuses:

- `proposed` — planned, not yet run;
- `running` — execution has begun;
- `review_pending` — outputs exist but human/reviewer interpretation is not complete;
- `supported` — the experiment produced evidence supporting its stated hypothesis under the recorded conditions;
- `insufficient` — the approach produced useful partial evidence but did not satisfy the experiment's acceptance condition;
- `superseded` — a later experiment replaces the execution path while preserving the earlier evidence;
- `failed` — the explicit experiment hypothesis/acceptance condition was contradicted or the run could not satisfy it for a documented reason.

Do not collapse `insufficient`, `superseded`, and `failed` into the same label. In particular, deterministic learning control remains an architectural authority boundary even when deterministic structure alone is insufficient to guarantee good tutoring.

## Active notebook

Model tutoring experiments are indexed at:

- `experiments/model-tutoring/README.md`
- `experiments/model-tutoring/manifest.json`
