# Interview Evidence and Adaptive Learning Plan

Status: proposed durable plan  
Date: 2026-09-02  
Scope: Study OS learner-facing interview preparation, curriculum evidence, and prospective adaptive-learning validation

## 1. Decision summary

Study OS will not try to become a replacement for LeetCode, Hello Interview, KodeKloud, or other curriculum providers.

Study OS is the learner-facing adaptive control plane over external tasks, open benchmarks, interview reports, labs, and the learner's longitudinal evidence.

Its job is to decide:

- what the learner should practice next;
- why that task is relevant to the learner's target roles;
- how much AI assistance is appropriate for the capability being tested;
- which representation or intervention to use when the learner gets stuck;
- when assistance should fade;
- whether the learner can later perform unaided;
- whether the capability transfers to a changed-surface problem;
- whether it is retained after delay.

External sources supply tasks, examples, labs, reported interview evidence, and reference material. Study OS owns the learner-state, intervention, assessment, transfer, and retention loop.

This plan deliberately separates two questions that must not be conflated:

1. **Curriculum relevance:** Are we teaching and testing capabilities that real hiring processes actually demand?
2. **Adaptive-learning effectiveness:** Given a relevant task, does Study OS choose interventions that improve the learner's later unaided performance, transfer, and retention?

A source can be excellent evidence for one question and weak evidence for the other.

## 2. Research hypotheses

### H1 — Curriculum relevance

Study OS can improve interview-preparation relevance by ranking tasks and competencies using explicit provenance from real interview reports, occurrence aggregates, current role requirements, and open expert-curated material rather than relying on a hand-built curriculum alone.

Evidence required:

- source-level provenance;
- role/company/round metadata where available;
- recency and frequency where available;
- explicit uncertainty when occurrence evidence is weak or absent.

### H2 — Adaptive-learning effectiveness

Study OS can improve learning efficiency by selecting assistance and representations from observed learner state, then fading that support and requiring later unaided reconstruction, transfer, and retention.

Evidence required:

- baseline attempt;
- failure classification;
- selected intervention and assistance level;
- immediate response;
- reduced-assistance or unaided retry;
- changed-surface transfer;
- delayed retention when appropriate.

Immediate success after a hint is useful evidence of an intervention response, but it is not sufficient evidence of durable learning.

## 3. Durable source registry

The verified source inventory and current ingestion decisions are maintained separately so this plan does not silently turn source assumptions into canonical contracts:

- human-readable decisions: `docs/INTERVIEW_SOURCE_REGISTRY.md`
- machine-readable registry: `datasets/interview-evidence/source-registry.json`

The registry records source class, provenance, occurrence strength, license/status, rights caveats, approved uses, and deferred/prohibited uses. It also preserves the rule that a repository license does not automatically grant rights to third-party content contained in that repository.

The source registry must be reviewed before adding any new corpus source or changing an ingestion policy.
