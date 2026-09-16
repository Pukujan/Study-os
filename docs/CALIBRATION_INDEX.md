# Study OS calibration index

This file is the repository-level discovery entrypoint for important learner-facing calibration evidence and golden fixtures.

Use this index when a fresh human or agent needs to find the canonical calibration source for a teaching behavior. Do not infer calibration authority from a filename such as `golden/` alone.

## Authority model

Study OS separates evidence from interpretation and executable authority:

```text
raw learner-visible evidence
    ↓
derived analysis / findings
    ↓
reviewed golden fixture(s)
    ↓
PIR-compiled reviewed trajectory
    ↓
runtime/controller authority
```

Rules:

- Read raw evidence before treating derived summaries or goldens as ground truth.
- A golden fixture may cover only part of a longer calibration session.
- `golden` means reviewed calibration fixture, not automatically complete transcript coverage or runtime authority.
- Runtime authority requires the evidence/compilation gates defined by the active P4/PIR specifications.
- Transcript success is learning/product evidence, not a mastery claim.

## Primary calibration datasets

### `sliding-window.subject-001.2026-09-04`

**Role:** primary learner-calibrated Sliding Window decomposition and pedagogical-control corpus.

**Canonical session root:**

`sessions/2026-09-04/sliding-window-pedagogy-calibration/`

**Session manifest:**

`sessions/2026-09-04/sliding-window-pedagogy-calibration/manifest.json`

**Raw source:**

`raw/chat-visible-transcript-part01.md` through `raw/chat-visible-transcript-part08.md`

The preserved verbatim-visible boundary begins at the earliest archived learner answer `6`. Earlier turns are continuity summary only and must not be represented as verbatim source evidence.

**Required read order for fresh analysis:**

1. `sessions/2026-09-04/sliding-window-pedagogy-calibration/manifest.json`
2. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part01.md`
3. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part02.md`
4. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part03.md`
5. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part04.md`
6. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part05.md`
7. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part06.md`
8. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part07.md`
9. `sessions/2026-09-04/sliding-window-pedagogy-calibration/raw/chat-visible-transcript-part08.md`
10. `sessions/2026-09-04/sliding-window-pedagogy-calibration/derived/pedagogy-findings.md`
11. `domains/dsa/sliding-window/golden/beginner-progressive-box-index-sum.v0.1.md`
12. `domains/dsa/sliding-window/golden/beginner-sum-enumerate-append.v0.1.md`

**Current golden status:** partial.

Existing reviewed fixtures cover the early foundation and the `sum → enumerate → append` continuation. The complete eight-part session contains additional calibrated material that has not all been promoted into reviewed golden fixtures, especially the later Python-loop assembly, max tracking, loop-combination/`else`, stop-condition, arbitrary-`k`, `range(k)`/`x`, and correction-policy sequences.

**PIR/runtime authority:** not complete. Issue #65 defines the lossless evidence-backed compilation program required before the complete September-4 golden trajectory is treated as authoritative controller input.

**Important interpretation:** this corpus is the calibration model for decomposition granularity and pedagogical control. It is not a universal hard-coded Sliding Window lesson template for every learner or every DSA problem.

## Adding future calibration datasets

Every calibration dataset promoted to this index should record at least:

- stable calibration ID;
- human-readable role/purpose;
- canonical session/evidence root;
- raw evidence boundary;
- exact raw transcript/artifact inventory or manifest pointer;
- required read order;
- derived-analysis paths;
- reviewed golden fixture paths;
- golden completeness status;
- runtime/PIR authority status;
- relevant issue/PR/spec governing promotion.

A dataset should not be listed as complete or runtime-authoritative merely because a derived fixture exists or an evaluator passes.
