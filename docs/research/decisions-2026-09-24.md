# Study OS product decisions — 2026-09-24

Durable record of Alex's post-review decisions after the SOS-0005 research gate ([#107](https://github.com/Pukujan/Study-os/issues/107)). Hypotheses and evidence stay in [`sos-0005-evidence-review.md`](./sos-0005-evidence-review.md). Voice stack detail lives in [`voice-robustness.md`](./voice-robustness.md). This file is the **decision log**; issue comments are not the source of truth.

Source comments (ET): [#107 Alex decisions](https://github.com/Pukujan/Study-os/issues/107#issuecomment-5823916572), [#107 H14/H15 addendum](https://github.com/Pukujan/Study-os/issues/107#issuecomment-5824369749), [#106 voice scope](https://github.com/Pukujan/Study-os/issues/106#issuecomment-5823918487), [#103 character roles](https://github.com/Pukujan/Study-os/issues/103#issuecomment-5824368687), [#101 companion update](https://github.com/Pukujan/Study-os/issues/101#issuecomment-5824369775).

| ID | Decision | Linked issues | Evidence / note |
|---|---|---|---|
| D1 | **Anime / sticker visual style: GO** via Pukujan/content-generation-modules (`.content-system/`), grown-up not childish; assets with provenance. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#103](https://github.com/Pukujan/Study-os/issues/103) | Overrides H7 "unknown/lean weak". Spec and sprites remain on draft PR #102 until Alex approves screenshots. |
| D2 | **No Netflix-style carousel** on home. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#101](https://github.com/Pukujan/Study-os/issues/101) | Aligns with H9 weak-at-current-scale. |
| D3 | **One home screen with all lanes** (DSA, HESI, AI from scratch, Study OS) and a single primary **Continue** action; fix HESI-only bug. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#105](https://github.com/Pukujan/Study-os/issues/105), [#101](https://github.com/Pukujan/Study-os/issues/101) | Aligns with H10. |
| D4 | **Companion panel on one screen**: question card always visible; panel opens beside (desktop) or as half-sheet (mobile). Variants / worked examples update the card **in place**. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#101](https://github.com/Pukujan/Study-os/issues/101) | H15 supported principle. Design §9 on draft PR #102 — not merged in this docs PR. |
| D5 | **Pet = chibi Learner (human)**; **robot = idle visitor only** (rare, never during assessment / typing). | [#107](https://github.com/Pukujan/Study-os/issues/107), [#103](https://github.com/Pukujan/Study-os/issues/103) | H14 weak-to-supported conditional. Character bible on draft PR #102. |
| D6 | **Voice = cheap, no paid speech models.** Browser TTS (`speechSynthesis`) + OS STT cascade where available; open fallbacks (transformers.js Whisper/Moonshine, faster-whisper on gravebuster). Optional I/O mode on suitable lessons, not a chatbot. **Cold-boot TTS voice dropdown** with lazy engines (see voice research §10). | [#107](https://github.com/Pukujan/Study-os/issues/107), [#106](https://github.com/Pukujan/Study-os/issues/106) | H11 stayed weak for a full agent; cheap optional mode approved. Full stack: [`voice-robustness.md`](./voice-robustness.md). |
| D7 | **Spoken-answer grading cascade:** rules / normalised match → MiniLM or bge-small vs expected answers and misconceptions → Jev when unsure; always-editable transcript; "did you mean…?". | [#106](https://github.com/Pukujan/Study-os/issues/106), [#107](https://github.com/Pukujan/Study-os/issues/107) | Detail in voice research §7. |
| D8 | **LLM-first with versioned prompts and full logging** (prompt version, PII-scrubbed I/O, model/route, tokens, cost, latency, validator, next-step outcome). Ground prompts in goldens/solutions from day one; cache proven outputs later. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#101](https://github.com/Pukujan/Study-os/issues/101), [#106](https://github.com/Pukujan/Study-os/issues/106) | Amends H12 ordering: grounded-first, then cache. |
| D9 | **Like / dislike (+ why) feedback** on every step and every tutor message; store with prompt version, model, step, session; admin or Metabase-ready SQL view. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#101](https://github.com/Pukujan/Study-os/issues/101) | Primary validation path without human spot-checkers. |
| D10 | **Goldens + conformance oracle as evals** (necessary, not sufficient); golden-replay agent evals with pass rates per prompt version; Alex live testing. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#101](https://github.com/Pukujan/Study-os/issues/101) | Aligns with H13. |
| D11 | Apply remaining evidence verdicts: fading micro-steps; representational learner-paced visuals; guarded grounded tutor chat (answer server-side); re-explain with **new example, same representation** first; lesson before signup / no tutorial deck; honour `prefers-reduced-motion`. | [#107](https://github.com/Pukujan/Study-os/issues/107), [#101](https://github.com/Pukujan/Study-os/issues/101) | H1–H6, H8. |

## Explicitly not decided / not landed here

- UX build, character assets, web/public art, and player design doc remain on **draft PR #102** until Alex approves screenshots. This docs PR does not merge them.
- Voice **implementation** is not started; only the research note is durable.
- Per-user accent LoRA: **not now** (voice research §8).

## How to cite

Prefer linking files under `docs/research/` on `main` over issue-comment URLs. When a decision changes, append a dated row here rather than editing history out of earlier rows.
