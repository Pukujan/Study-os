# TASK-SOS-0009 — Voice robustness research (STT/TTS)

<!-- continuity:task {"acceptance":["docs/research/voice-robustness.md covers STT landscape, front-end audio, context biasing, post-processing/grading, personal adaptation, TTS (incl. expressive anime-style English under licence constraints), cold-boot voice dropdown design, browser vs gravebuster, privacy, licences, recommended stack with fallbacks, and a small benchmark plan","claims cite model cards, papers, benchmarks or measured box/gravebuster checks; aim ≥25 sources","recommended stack and key findings posted on #106","no build, no production change, SOS-0005 branch untouched","validate_repo / unittest / pinned PCM preflight stay green if run"],"depends_on":[],"goal":"Research how to make open-source STT/TTS smarter under bad mics, noise and accents for Study OS voice mode, and design a cold-boot TTS voice dropdown.","id":"SOS-0009","issue_url":"https://github.com/Pukujan/Study-os/issues/106","next_action":"Alex reviews docs/research/voice-robustness.md and the /workspace/voice-samples TTS clips; choose STT A/B (Moonshine browser vs faster-whisper small.en+hotwords vs Parakeet) and which TTS engines to enable after gravebuster tts-bench.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0009-voice-robustness-research","priority":"P2","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"active","why":"Alex wants voice as an optional lesson mode. Open STT/TTS fail on bad mics, noise and accents; Study OS also wants an expressive non-robotic tutor voice without cloning real actors, plus a dropdown of all viable TTS engines cold-booted on demand."} -->

- Status: active
- Owner: Pukujan (GitHub assignee)
- Priority: P2
- Depends on: none
- Branch: `task/SOS-0009-voice-robustness-research`
- GitHub issue (leaf): #106 — parent: #82 (web-app epic) — research umbrella: #107 — dependencies: none

## Goal

Research how to make open-source STT/TTS smarter under bad mics, noise and accents for Study OS voice mode, and design a cold-boot TTS voice dropdown.

## Why

Alex wants voice as an optional lesson mode. Open STT/TTS fail on bad mics, noise and accents; Study OS also wants an expressive non-robotic tutor voice without cloning real actors, plus a dropdown of all viable TTS engines cold-booted on demand.

## Human outcome

Alex can decide in one read: STT stack and fallbacks, front-end audio policy, grading cascade, whether per-user LoRA is worth it, TTS default + expressive options with licences, cold-boot dropdown architecture on gravebuster, and the next measurement to run.

## Allowed files

- `docs/research/voice-robustness.md` (new)
- `tasks/TASK-SOS-0009-voice-robustness-research.md`
- `docs/HANDOFF.md` (short pointer only)

## Scope and boundaries

- In scope: cited research note, recommended stack with fallbacks, benchmark plan, optional box smoke tests and TTS sample clips, comments on #106 / #107.
- Out of scope: app code, production deploy, SOS-0005 branch / PR, paid speech APIs, cloning real voice actors or copyrighted anime characters.
- Dependencies/uncertainty: box CPU ≠ gravebuster CPU; Chatterbox latency on gravebuster still gated by the §10.5 acceptance bar.

## Acceptance criteria

- [x] Research note at `docs/research/voice-robustness.md` with the required sections and ≥25 cited sources.
- [x] Recommended stack + dropdown design + benchmark plan included.
- [x] Start comments on #106 and #107; summary comment after push.
- [x] SOS-0005 and production untouched.
- [ ] PR opened with `Refs #106` only (no closing keywords).

## Checkpoint log

### 2026-09-24 — research draft

Completed:
- Surveyed STT/TTS landscape; measured EdAcc/Libri/HESI smoke on the box; generated Kokoro/Pocket/Piper samples; designed cold-boot TTS router; wrote `docs/research/voice-robustness.md`.

Decisions:
- Default STT path: browser Moonshine (or Whisper small.en) with lesson hotwords; gravebuster fallback faster-whisper `small.en` + hotwords or Parakeet-TDT int8.
- Default TTS: always-warm Kokoro; Pocket TTS (CC0/CC-BY voices) and Piper as lazy dropdown engines; exclude NC weights (F5, XTTS).
- Per-user LoRA deferred until key-term error stays >15% after biasing + matching.

Blocked/uncertain:
- Chatterbox warm p95 on gravebuster under real load not yet measured (enable only if it clears §10.5).
- Box float32 numbers are indicative; gravebuster int8 determinism must be re-checked.
- Moonshine medium-streaming offline decode was unreliable on the box.

Next:
- Push branch, open PR with `Refs #106`, post summary on #106.

Evidence:
- gravebuster read-only hardware check (Ryzen 7 5800U, no NVIDIA, load 30–51).
- Box STT table in the research note §3; TTS samples under `/workspace/voice-samples/`.
