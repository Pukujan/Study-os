# `docs/research/` — durable research source of truth

This directory is the **durable home** for Study OS research notes and decision logs that used to live only in GitHub issue comments or on feature branches.

| File | What it is | Issues |
|---|---|---|
| [`sos-0005-evidence-review.md`](./sos-0005-evidence-review.md) | SOS-0005 research gate: 15 hypotheses, verdicts, 86 sources | [#107](https://github.com/Pukujan/Study-os/issues/107) |
| [`voice-robustness.md`](./voice-robustness.md) | SOS-0009 voice robustness (authoritative from `62f1969` / PR #109): STT/TTS stack, biasing, grading cascade, cold-boot TTS dropdown, box measurements | [#106](https://github.com/Pukujan/Study-os/issues/106), [#107](https://github.com/Pukujan/Study-os/issues/107), [#109](https://github.com/Pukujan/Study-os/pull/109) |
| [`decisions-2026-09-24.md`](./decisions-2026-09-24.md) | Alex's post-review product decisions (incl. **product moat**: multi-representation + stepwise pedagogical goals; anime via CGM; no Netflix carousel; companion; voice stack; LLM logging; feedback; goldens-as-evals) | [#107](https://github.com/Pukujan/Study-os/issues/107) and linked leaves |

## Rules

1. **Research and decisions land here on `main`.** Issue threads track progress and point here; they are not the long-term store.
2. **Design / build documents** (player design, character bible, UX shots) stay on their task branches / draft PRs until Alex approves. Do not treat draft PR #102 as merged research.
3. New research notes: add a file under this tree, link it from this README, and use `Refs #N` (never Close/Fix/Resolve) on the PR.
4. When Alex decides, append to a dated decisions file (or a new dated file) and link the evidence note that informed it.

Draft UX work continues on `task/SOS-0005-lesson-player-redesign` (PR #102) and is out of scope for this tree until approved.

- [`pedagogical-decomposer.md`](./pedagogical-decomposer.md) — SOS-0011 research gate (CTA/ITS/representations/LLM curricula; recovery test; architecture).
- [`decomposer-review/`](./decomposer-review/) — human-eval UI data + mirror of `/review/decomposer`.
