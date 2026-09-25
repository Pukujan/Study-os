# Study OS pedagogy moat (Alex, 2026-09-04 calibration)

Status: durable statement extracted from the sliding-window pedagogy transcript and goldens.
Do not treat the short golden markdown files as sufficient alone — the long transcript is the teaching pattern source.

## Moat statement

Study OS's teaching moat is **multiple representations + stepwise pedagogical goals**, under a deterministic controller:

1. **Stable representation** — Prefer the same small ASCII box/index chart (numbers, index row, box, k) while a relation is being learned. Do not switch to detached algebra, mermaid dumps, or text walls mid-step.
2. **One new relation at a time** — Each step has exactly one pedagogical goal the learner must demonstrate before advancing.
3. **Charts carry meaning** — The diagram is part of explanation and validation, not decoration.
4. **Exercise ≠ intro cues** — Intro/correction may use arrows/circles; exercises strip answer-revealing cues while keeping the same representation.
5. **Feedback loop** — Correct → show why on same chart. Wrong → give answer, show why on same chart, reassure, different retry, verify again, then advance.
6. **Process before symbols** — see process → understand relation → name parts → write equation/code (not the reverse).
7. **Multi-representation playbook** — ASCII box/index for in-step DSA state; mermaid/lesson-map trees for path overview only; code trees for enumerate/append/loop assembly; worked examples as brief equivalences; companion talk kept short.
8. **No mastery claim from calibration** — Exit as assembled-but-unproven; never claim mastery from one session.

## Why this is a moat

Public tutoring datasets (MathDial, ASSISTments, Eedi) cover dialogue, retries, or misconceptions separately. They do **not** cleanly encode this exact controller **plus** the representation shown at every step. Study OS owns that missing layer via transcript-grounded goldens and this dataset.

## Citations (sample)

- part02 ~L2271: one concept → tiny diagram → one exercise → wrong: explain just that mistake → retry → another correct → advance
- part02 L1845/1865: mermaid rejected; ASCII diagram preferred
- part03 L729-731: arrow rules
- part06 L81-123: exercise/correction chart stages
- part06 L758-776: multiple representations cross-check (physics analogy)
- part08 L3589-3634: representation stability, one relation, repair only the failed bridge
- `docs/PROJECT_BOUNDARY.md`: representation families and transitions

## Related fixtures

- `domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md`
- `domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md`
- `domains/dsa/sliding-window/golden/dataset/` (this extract)
