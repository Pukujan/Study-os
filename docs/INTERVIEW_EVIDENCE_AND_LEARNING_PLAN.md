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

## 3. Operating principles

### 3.1 Evidence before taxonomy

Do not hard-code a complete interview curriculum or AI-delegation policy from intuition.

Use external evidence to estimate what capabilities are actually demanded. Use the learner's own longitudinal outcomes to personalize how those capabilities should be learned.

### 3.2 Population prior, learner posterior

External data provides a population-level prior such as:

- which competencies appear in target-role interviews;
- which tasks are recent or frequently reported;
- which rounds tend to require unaided implementation, design, explanation, or debugging.

The learner's evidence then updates the policy.

A capability that is normally AI-assisted may still require more manual practice for a learner who repeatedly fails to understand or modify generated implementations. A capability that is rarely tested unaided should not automatically consume large amounts of memorization time.

### 3.3 Technical ownership is distinct from manual construction

Study OS must not assume that learning requires manually constructing every artifact from scratch.

It should track at least two distinct capability dimensions:

- **unaided capability:** can the learner produce the required reasoning or implementation without external assistance when the target context demands it?
- **AI-augmented ownership:** can the learner understand, inspect, modify, debug, verify, and defend an AI-assisted implementation?

The required balance is task- and interview-dependent and should be evidence-driven.

### 3.4 Provenance is mandatory

Every imported or referenced task must preserve its source class and source identity. Study OS must not erase whether a task came from:

- a candidate-reported real interview;
- an occurrence aggregate;
- an expert-curated open curriculum;
- an open synthetic benchmark;
- a private/commercial study source;
- Study OS synthetic generation.

### 3.5 Do not collapse evidence classes

The following statements are different and must remain different in storage and reporting:

- "A candidate reported being asked this question."
- "This question is associated with this company in a frequency dataset."
- "An expert-curated curriculum recommends this competency."
- "This is a synthetic transfer task."
- "The learner solved this after a hint."
- "The learner solved a changed problem unaided."
- "The learner retained the capability after delay."

## 4. Source and evidence hierarchy

Study OS will use multiple source classes because no single public dataset currently provides verified interview occurrence, open licensing, rich rubrics, broad AI/ML coverage, and longitudinal learner outcomes.

### Class A — Reported real interviews

Examples:

- public candidate interview-experience reports;
- structured public community reports;
- company/role/round records with source URLs.

Purpose:

- strongest available signal that a topic or task actually appeared in a hiring process;
- round structure;
- company/role/seniority context;
- whether AI was allowed or disallowed when explicitly reported.

Limitations:

- self-reported;
- incomplete;
- potentially noisy or inaccurate;
- publication rights for the original prose may differ from rights to store structured observations.

Required labels:

- `source_type = candidate_report`
- `occurrence_evidence = reported`
- `provenance_quality = self_reported` unless independently verified

### Class B — Interview occurrence aggregates

Examples:

- company-tagged coding-question datasets;
- datasets with frequency, timeframe, or recency buckets;
- public question indexes with report counts.

Purpose:

- prioritize DSA/coding problems by company and recency;
- estimate relative occurrence rather than treating all practice questions equally.

Limitations:

- company tags and frequencies may derive from proprietary or community platforms;
- exact derivation and reuse rights must be recorded per dataset;
- association is not proof of a specific interview event.

Required labels:

- `source_type = occurrence_aggregate`
- `occurrence_evidence = aggregate`

### Class C — Open expert-curated curriculum

Examples currently worth evaluating for ingestion:

- AIMLInterviews;
- open AI Engineering interview question repositories;
- open ML interview question repositories;
- ML-InterviewQs and similar reviewed/open banks.

Purpose:

- competency coverage;
- explanations;
- interview-oriented question generation;
- gap detection in AI/ML/system-design curricula.

Limitations:

- expert relevance is not equivalent to observed interview frequency;
- each repository's exact license and version must be captured at ingestion time.

Required labels:

- `source_type = expert_curated`
- `occurrence_evidence = none` unless a separate occurrence source supports it

### Class D — Open synthetic or benchmark material

Examples currently worth evaluating:

- ML Systems Interview Bench;
- other openly licensed benchmark/question datasets with rubrics and reference answers;
- Study OS generated transfer variants derived from open concepts.

Purpose:

- reproducible assessment;
- rubrics;
- transfer testing;
- controlled variation;
- replay and evaluation.

Limitations:

- synthetic questions are not evidence that companies ask them;
- benchmark difficulty may not be empirically calibrated.

Required labels:

- `source_type = open_synthetic` or `study_os_synthetic`
- `occurrence_evidence = none`

### Class E — External/private study sources

Examples:

- Hello Interview;
- KodeKloud labs;
- paid courses;
- other learner-authorized private materials.

Purpose:

- ecologically valid learning tasks;
- realistic labs;
- high-quality explanations and breakdowns;
- interview-shaped practice chosen by the learner.

Rules:

- preserve the original source and task reference;
- use the material during the learner's legitimate private study session;
- store primarily learner-generated evidence, normalized competency mappings, source metadata, and permitted excerpts/metadata;
- do not assume a paid subscription grants permission to bulk scrape, republish, or build a local replacement corpus;
- record source-specific usage restrictions before automated ingestion.

Required labels:

- `source_type = external_private`
- `content_storage_policy` must be explicit

## 5. Initial source registry candidates

The following are candidates, not automatically trusted canonical sources. Each must be verified at the exact commit/version used.

| Source | Intended role | Initial evidence class | Ingestion note |
| --- | --- | --- | --- |
| CodeJeet / company-wise coding datasets | DSA occurrence/frequency | B | verify row provenance and license boundary |
| recent company-wise LeetCode datasets | DSA recency/frequency | B | preserve timeframe and original provenance |
| InterviewDrip-style extraction from public candidate reports | real interview observations | A | software license does not automatically license candidate prose |
| AIMLInterviews | AI/ML interview curriculum | C | capture exact repository license/version |
| open AI Engineering interview question banks | applied-AI competency coverage | C | capture exact repository license/version |
| open ML interview question banks | ML/MLOps/system-design coverage | C | capture exact repository license/version |
| ML Systems Interview Bench | structured rubric/schema inspiration | D | synthetic; never report as observed hiring frequency |
| Hello Interview public/community index | report-count/recency/task reference | A/B depending on field | respect site terms and source-specific storage policy |
| learner-authorized Hello Interview premium material | private study source | E | session-level use; no assumption of bulk corpus rights |
| KodeKloud labs | engineering/MLOps task source | E | task references + learner evidence; no assumption of bulk corpus rights |

## 6. Canonical task evidence model

This is a planning model, not yet an implementation commitment. Existing canonical Study OS contracts remain authoritative until a schema change is explicitly designed and reviewed.

A normalized task should be able to represent fields conceptually equivalent to:

```yaml
task_id: string

source:
  source_name: string
  source_url: string | null
  source_type: candidate_report | occurrence_aggregate | expert_curated | open_synthetic | external_private | study_os_synthetic
  source_version: string | null
  license_or_usage_status: string | null
  content_storage_policy: full | metadata_only | reference_only | learner_derived_only | unknown

interview_evidence:
  company: string | null
  role: string | null
  seniority: string | null
  round_type: string | null
  reported_date: date | null
  report_count: integer | null
  recency_bucket: string | null
  occurrence_evidence: reported | aggregate | none
  evidence_confidence: string | null

task:
  task_type: string
  competencies: [string]
  difficulty: string | null
  expected_reasoning: [string]
  reference_answer_ref: string | null
  rubric_ref: string | null

learning_policy:
  unaided_requirement: unknown | low | medium | high
  allowed_assistance: [string]
  representation_candidates: [string]
  policy_basis: [string]
```

Important constraints:

- fields may be null;
- missing metadata must not be guessed;
- occurrence evidence is independent of task quality;
- `unaided_requirement` is a policy estimate, not an intrinsic property of the concept;
- policy estimates must preserve the evidence used to derive them.

## 7. Learner episode model

Study OS's most valuable proprietary/private dataset is the learner's own longitudinal learning evidence.

The prospective episode should preserve at least the dimensions already identified in Study OS methodology work:

```yaml
learner_episode:
  task_id: string
  attempt_sequence: integer
  outcome: string
  assistance_level: string
  representation: string | null
  effort_mode: string | null
  failure_signature: [string]
  candidate_state: string | null
  internalization_result: string | null
  checkpoint_ref: string | null
```

For prospective validation, extend the episode conceptually with explicit follow-up outcomes:

```yaml
validation:
  reduced_assistance_result: string | null
  unaided_result: string | null
  transfer_task_id: string | null
  transfer_result: string | null
  retention_probe_id: string | null
  retention_result: string | null
  retention_delay: string | null
```

The exact implementation must be reconciled with existing Study OS application contracts rather than creating a parallel state model.

## 8. Curriculum relevance evaluation

Study OS should eventually estimate task priority from evidence rather than static lists.

A conceptual ranking model may consider:

```text
priority =
    target_role_match
  × interview_occurrence_signal
  × recency_signal
  × learner_gap
  × transfer_value
  × prerequisite_readiness
  × time_budget
```

This is not a committed formula. The purpose is to make the factors explicit and empirically inspectable.

Questions to evaluate:

- Does the selected curriculum cover capabilities appearing in target AI/ML engineering interviews?
- Are high-frequency/recent competencies over- or underrepresented?
- Does Study OS distinguish DSA, backend coding, AI-assisted coding, ML fundamentals, RAG, agents, evals, AI/ML system design, general system design, debugging, deployment/MLOps, and behavioral communication when the evidence supports those distinctions?
- Does it avoid spending disproportionate time on low-value syntax/tool memorization when the target hiring process does not require unaided recall?

## 9. Adaptive-learning experiment

### Phase 0 — Preserve retrospective evidence

Treat existing FOSSIL/Study OS methodology capture as hypothesis-generating evidence, not proof of durable learning.

The retrospective evidence can inform candidate interventions and failure signatures, but prospective sessions must produce new outcome measurements.

### Phase 1 — Build a small provenance-complete corpus

Do not begin with maximum volume.

Create a v1 corpus sufficient to cover major target domains:

- DSA/coding;
- Python/backend/software engineering;
- AI/LLM fundamentals;
- RAG/retrieval;
- agents/tool use;
- evals;
- ML fundamentals;
- ML system design;
- general system design;
- MLOps/deployment;
- debugging/observability;
- behavioral and technical communication.

A smaller corpus with explicit provenance is preferable to a large mixed corpus whose source and evidence status are unclear.

### Phase 2 — Baseline

For selected tasks, obtain an initial attempt before substantive intervention where practical.

Record:

- task and source;
- learner response;
- elapsed/active time if reliable instrumentation exists;
- outcome;
- failure signature;
- confidence/effort/clarity when useful and not burdensome;
- assistance already present in the environment.

### Phase 3 — Adaptive intervention

Run the Study OS loop:

```text
task
  -> baseline attempt
  -> classify observed bottleneck
  -> choose representation/assistance
  -> retry
  -> reduce assistance
  -> unaided reconstruction
  -> changed-surface transfer
  -> delayed retention when appropriate
```

Candidate intervention dimensions include:

- prose explanation;
- concrete example;
- pseudocode;
- ASCII/tree representation;
- execution/state trace;
- architecture diagram;
- code reading;
- code modification;
- prediction before execution;
- syntax-only correction;
- conceptual hint;
- partial solution;
- full solution only when necessary.

The system should not reveal or force an intervention merely because that intervention performed well once in retrospective data.

### Phase 4 — Compare prediction with outcome

The important unit of evidence is:

```text
learner state + failure evidence
  -> Study OS predicts intervention X is useful
  -> X is delivered
  -> downstream behavior is measured
  -> assistance is faded
  -> transfer/retention is measured
```

This supports live-shadow evaluation of adaptive proposals before granting stronger automated authority.

### Phase 5 — Replay and policy evaluation

Once enough episodes exist:

- freeze a replay corpus;
- compare alternate selectors/intervention policies against recorded state;
- inspect whether proposed choices would have differed;
- compare policy recommendations with actual downstream outcomes where counterfactual inference is defensible;
- do not claim causal superiority from observational comparisons alone.

## 10. Success criteria

A learner-facing adaptive episode counts as stronger evidence when Study OS:

1. correctly resumes relevant learner context;
2. identifies a specific observed bottleneck rather than generic wrongness;
3. selects an intervention with an explicit evidence basis;
4. the learner improves on the immediate task;
5. the aid is reduced or removed;
6. the learner succeeds unaided or with less assistance;
7. the learner succeeds on a changed-surface transfer task;
8. delayed retention is preserved when the skill warrants retention testing.

The target for this phase is repeated evidence across more than one failure type, not a single successful episode.

## 11. What does not count as proof

Study OS must explicitly reject the following shortcuts:

- an AI-generated implementation completing successfully does not prove learner mastery;
- a learner saying an explanation felt helpful does not prove retention;
- a successful retry immediately after a hint does not prove durable learning;
- a candidate interview report does not define official company interview policy;
- a company tag does not prove an exact question was asked in a specific interview;
- a synthetic benchmark question does not prove market relevance;
- a large question bank does not prove curriculum quality;
- a high mastery score without preserved behavioral evidence does not prove capability;
- one learner's trajectory does not support population-level learning-effect claims.

## 12. External-source usage policy

### Open-licensed sources

When license terms permit:

- ingest full records;
- preserve license and version;
- normalize into canonical task records;
- generate variants;
- use in replay and benchmark evaluation;
- retain original source references.

### Public candidate reports

Prefer structured observations with source URLs over republishing report prose.

Store fields such as:

- company;
- role;
- seniority;
- round;
- reported topic/task signature;
- reported AI allowance if explicit;
- report date;
- source URL;
- confidence/provenance status.

### Commercial/private curriculum

For sources such as Hello Interview and KodeKloud:

- use tasks during legitimate private study;
- preserve task/source references;
- store learner attempts, explanations, failure evidence, competency mappings, and outcomes;
- only store original source content to the extent permitted by the applicable terms/authorization;
- do not design automated bulk ingestion until source-specific usage rights have been reviewed;
- do not make Study OS a substitute republished corpus.

### Study OS synthetics

Synthetic tasks must record:

- the competencies they are intended to test;
- the source concepts/evidence that motivated generation;
- that the task is synthetic;
- whether it is a near-transfer or far-transfer variant;
- any reference/rubric generation provenance.

## 13. Privacy and public-repository boundary

The Study OS source repository is public. Learner operational state and private curriculum content must not accidentally become public repository artifacts.

Before committing any dataset or source record to the public repository, classify whether it contains:

- private learner data;
- direct transcript content;
- paid/proprietary course content;
- credentials/tokens;
- personally identifying information;
- copyrighted source text whose redistribution status is unclear.

Public repository artifacts should prefer:

- schemas;
- ingestion code;
- open-licensed fixtures;
- public-safe metadata;
- synthetic examples;
- documented source references;
- aggregate/non-sensitive evaluation outputs.

Operational learner evidence remains subject to the existing Study OS local/private evidence boundary.

## 14. Engineering sequence

Do not resume broad architecture expansion merely because this plan exists.

The next engineering work should be driven by what the experiment needs.

### Step 1 — Source registry

Create a machine-readable registry that records, at minimum:

- source identifier;
- evidence class;
- URL/repository;
- exact version/commit when applicable;
- license or usage status;
- allowed storage/transformation mode;
- provenance notes.

### Step 2 — Small v1 corpus

Ingest a deliberately small set from Classes A-D with clear provenance.

Include at least:

- company/recency-aware DSA data;
- real candidate-reported AI/ML interview observations;
- open AI/ML interview curriculum;
- an open structured ML/system-design benchmark with rubrics.

Class E sources can be referenced during live learning without requiring bulk ingestion.

### Step 3 — Normalize without losing evidence

Build or extend normalization only after inspecting real source shapes.

Do not force all sources into a lossy question/answer pair.

Preserve source-specific fields needed for:

- occurrence;
- recency;
- role/round context;
- competency mapping;
- rubrics;
- rights/provenance.

### Step 4 — Verify learner-facing capture

Before running the experiment, verify that the actual learner-facing Study OS path can durably record the fields necessary to reconstruct:

```text
task
-> attempt
-> failure
-> intervention
-> retry
-> fade
-> unaided result
-> transfer
-> retention
```

If the runtime cannot preserve this sequence, fix the smallest blocking gap first.

### Step 5 — Run real sessions

Run several real Study OS learning episodes using tasks from the provenance-complete corpus and learner-authorized external sources.

The learner should learn normally; the experiment should not force artificial representations merely to create data.

### Step 6 — Evaluate before expanding

Use the observed failures to determine the next engineering priority.

Possible outcomes:

- if task selection is poor, improve curriculum evidence/ranking;
- if interventions are generic, improve learner-state projection or intervention selection;
- if assistance does not fade, fix tutoring policy;
- if transfer/retention is not scheduled or recorded, fix assessment lifecycle;
- if runtime persistence breaks continuity, prioritize persistence/application-boundary reliability;
- if the loop works repeatedly, proceed toward broader live-shadow evaluation and later advisory/canary authority under existing verification gates.

## 15. Non-goals for this phase

This phase is not intended to:

- scrape every interview or course website;
- build a universal curriculum ontology before seeing source data;
- replace Hello Interview, KodeKloud, LeetCode, or other platforms;
- prove population-level educational efficacy from a single learner;
- optimize every curriculum category simultaneously;
- memorize all operational syntax/tooling;
- grant unrestricted runtime authority to an adaptive selector;
- claim causal learning gains from retrospective conversation evidence alone.

## 16. Immediate deliverables

The next concrete artifacts should be:

1. a source registry with verified license/usage/provenance metadata;
2. a small v1 interview-evidence corpus with explicit evidence classes;
3. a normalization design based on the actual source records rather than an invented universal schema;
4. a verification that the learner-facing Study OS runtime captures the required prospective episode fields;
5. several real dogfooding episodes with baseline, intervention, assistance fade, transfer, and retention evidence;
6. a report comparing Study OS intervention predictions with observed downstream learner behavior.

## 17. Decision gate

Do not call Study OS's adaptive-learning mechanism validated merely because the corpus is large or the app feels personalized.

Proceed to stronger adaptive authority only when prospective learner episodes repeatedly show that Study OS can use preserved learner evidence to change instruction in a relevant way and that the resulting capability survives reduced assistance, transfer, and—where appropriate—delayed retention.

Until then, the correct status is:

> **evidence-backed curriculum discovery + prospective adaptive-learning validation in progress**
