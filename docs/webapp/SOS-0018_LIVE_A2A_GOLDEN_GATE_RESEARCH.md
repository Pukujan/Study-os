# SOS-0018 live A2A golden roleplay gate: evidence base (A9b)

Status: research/planning only, issue #126. Companion docs: `SOS-0018_LIVE_A2A_GOLDEN_GATE_PDD.md` (requirements), `_SDD.md` (design), `_TDD.md` (RED contract). Nothing here changes product code, schema versions, evidence classes, or the research gate.

## Question

A6/A7 assert `regenerate_presentation` detectors and A8 asserts the typed 1-5 + Submit contract. `tests/test_pir_golden_conformance.py` proves the **asset** matches the golden oracle, but it is a controller/asset oracle over a static fixture, not two agents in conversation. The remaining unknown before human testing is: **does the live, InferHub-backed tutor still obey the golden bridge order, the one-new-concept rule, the no-answer-leak rule and the re-render invariants when a realistic (including adversarial) learner drives it over HTTP?** That is a behavioural question about a stochastic component, so it needs live roleplay, not more static assertions.

## Claims and sources

| # | Claim relied on | Source |
| --- | --- | --- |
| E1 | Agent capability must be measured by task completion over full interactions, not single-turn accuracy; simulated users plus deterministic checks are the standard shape. | AgentBench, https://arxiv.org/abs/2308.03688 |
| E2 | Simulated-user agent evaluation should report reliability across repeated trials (`pass^k`), because one success in a stochastic system is dominated by chance. | tau-bench, https://arxiv.org/abs/2406.12045 |
| E3 | Behavioural testing needs relation families - invariance (perturbation must not change the label), directional (perturbation must change it), minimum functionality - each with an explicit expected outcome. | CheckList, https://arxiv.org/abs/2005.04118 |
| E4 | An LLM judge is usable as *corroborating* evidence only; it carries position, verbosity and self-enhancement bias, so it cannot be the sole gate. | MT-Bench / LLM-as-a-judge, https://arxiv.org/abs/2306.05685 |
| E5 | Learner-facing text can carry injected instructions, so an adversarial persona belongs in the suite and injection resistance must be asserted deterministically. | Greshake et al., https://arxiv.org/abs/2302.12173 |
| E6 | Tutor quality is rubric-gradable along pedagogical axes (not revealing the answer, building on prior thinking, one new idea at a time), which is what our detectors mechanise. | LearnLM, https://arxiv.org/abs/2409.01653 |
| E7 | Live web-app agents are evaluated against a running app with a real backend and a throwaway environment; the harness must not mutate production state. | WebArena, https://arxiv.org/abs/2307.13854 |
| E8 | Metamorphic relations are the accepted way to test systems without a per-input oracle; this gate reuses the framing already pinned for SOS-0017 rather than inventing a new one. | survey as cited in `docs/webapp/SOS-0017_E2E_VISION_GATE_RESEARCH.md` (https://arxiv.org/abs/2605.13898) |
| E9 | Local, already-landed harness facts: deterministic detectors per turn, tiered budgets, synthetic-only output never written to `learn.*`, stub tutor by default with `STUDY_OS_EVAL_LIVE=1` opt-in. | `docs/webapp/AGENT_EVAL.md` (repo-relative, authoritative for our conventions) |

E1-E8 are external literature; E9 is this repository's own contract and wins on any conflict about Study OS behaviour.

## What the evidence does **not** support

- It does not support treating a green roleplay as human learning evidence. Synthetic transcripts are system evaluation only; the manifest prohibited claim `synthetic_simulation_equals_human_learning_effect` still binds (`PROJECT_MANIFEST.yaml`).
- It does not support a causal claim about any representation. A green live gate shows the tutor obeyed the contract under these personas and seeds; it does not show one representation teaches better than another (AGENTS.md: record confounds, avoid implied causality).
- It does not license an LLM judge as the pass/fail authority (E4). Judges may only *add* findings; deterministic detectors decide.
- It does not generalise beyond sliding-window / `subject-001` scope. Per AGENTS.md, subject-specific observations do not become universal lesson claims.
- Simulated-user fidelity is a known limitation (E2): passing personas are necessary, not sufficient, for a good human session. Human testing still follows.

## Why a live gate now, and why still cheap

AGENT_EVAL's tiering already answers this: T0 runs every PR at zero cost against recorded fixtures/stubs, T1 is the capped live run (cap 0.50 USD/run, expected under 0.05 USD). SOS-0018 is the **T1-shaped live gate** for the player route: runnable on demand against `TEST_DATABASE_URL` with `STUDY_OS_EVAL_LIVE=1`, out of the always-on CI path, and emitting a receipt a human or watcher can audit. Keeping live opt-in preserves the zero-cost default and keeps CI deterministic.

## Prior art inside this repo (do not duplicate)

- `tools/run_player_agent_evals.py` - scripted learner/tutor roleplay, `golden_prefix()` oracle pin, `capability_detector()` for `regenerate_presentation`, `review_event_detector()`, per-persona synthetic client IPs, `study-os.player-agent-evals.v1` scorecard.
- `tests/test_player_agent_evals.py` - persona determinism, oracle prefix, IP stability, missing-render failure.
- `domains/dsa/sliding-window/golden/conformance-oracle.v0.1.json` plus the two golden markdown lessons - the bridge/answer oracle.
- `tests/test_pir_golden_conformance.py` - asset-level conformance (controller oracle, not live chat).
- `docs/webapp/SOS-0016_STEP_REVIEW_{PDD,SDD,TDD}.md`, `docs/webapp/SOS-0017_E2E_VISION_GATE_{RESEARCH,PDD,SDD,TDD}.md` - doc and RED-contract style this gate follows.

SOS-0018 extends the harness with a gate mode, more personas, more detectors, a seed/reliability policy, metamorphic relations, hidden holdouts and an auditable live receipt. It replaces none of the above.
