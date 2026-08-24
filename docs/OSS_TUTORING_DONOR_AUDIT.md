# OSS Tutoring Donor Audit

Status: **research/design input; not an implementation decision**

Last updated: 2026-08-24

## Question

Which open-source systems and research implementations should Study OS treat as the strongest donors or benchmarks for:

- LLM tutoring policy;
- representation-based learning;
- atomic competency decomposition and prerequisite progression;
- difficulty/complexity adaptation;
- candidate concept/task/test ranking;
- mastery, retention, transfer, and misconception tracking;
- tutor-behavior evaluation?

## Executive conclusion

There is no single OSS project that should replace Study OS or serve as the sole highest-ranked source. The strongest evidence points to a **layered donor stack** because the relevant problems are distinct.

Recommended source classes by subsystem:

1. **Learner-state regulation / next-action control:** Tutor MCP.
2. **Stepwise LLM pedagogical planning and turn-by-turn assessment:** ScaffoldLM.
3. **Atomic curriculum / prerequisite / misconception / scaffolding model:** Oppia and OATutor.
4. **Candidate assessment-item ranking and psychometric information gain:** catsim and EduCAT; BOBCAT/BECAT as later research references.
5. **Mature agent-native LLM tutoring shell and mastery gates:** DeepTutor.
6. **Tutor-behavior training/evaluation:** PedagogicalRL and MathTutorBench.
7. **Representation-generation and multimodal-learning efficacy benchmark:** Google Learn Your Way (not OSS; research benchmark only).
8. **Retention scheduling:** FSRS implementations.
9. **Knowledge tracing:** pyBKT for interpretable BKT; pyKT as a benchmark suite rather than an immediate production dependency.

Study OS should preserve its existing evidence/provenance/checkpoint and representation-intervention semantics. Those remain differentiators not cleanly supplied by the donor projects above.

## Evaluation axes

Do not rank projects by GitHub stars alone. Evaluate each source separately on:

- scientific evidence strength;
- implementation maturity;
- architecture fit;
- code/license transplantability;
- learner-model transparency;
- deterministic testability;
- support for N=1 longitudinal evidence;
- support for representation-effect measurement rather than fixed learning-style labels.

## Tutor MCP — strongest control-loop donor

Repository: https://github.com/ArnaudGuiovanna/tutor-mcp

Tutor MCP is unusually close to the Study OS control problem. Its regulation pipeline separates goal decomposition, concept selection, action selection, gates, phase control, fading, and learner state.

### LLM role

The LLM is deliberately treated as a content/pedagogical engine rather than the sole policy core. For example, the LLM writes a versioned per-concept `goal_relevance` vector through a semantic tool. The runtime validates that concepts exist and then consumes the vector deterministically.

This is a useful pattern for Study OS: let the LLM propose semantic judgments, but validate and version them before they influence policy.

### Candidate concept ranking

Tutor MCP separates phases:

- **Instruction:** compute the external prerequisite fringe, then score eligible concepts approximately as `goal_relevance * (1 - mastery)`.
- **Maintenance:** among mastered concepts, calculate FSRS retrievability/forgetting urgency, then weight by goal relevance.
- **Diagnostic:** select uncertain concepts using expected BKT information gain, i.e. expected entropy reduction after the next response.

This is directly relevant to Study OS's future `next high-information probe` policy.

### Difficulty/action progression

Tutor MCP's action selector uses state-dependent branches:

- active misconception -> targeted debugging;
- low retention -> recall;
- low mastery -> concept introduction;
- intermediate mastery -> practice;
- near mastery -> IRT/ZPD-calibrated practice;
- high mastery -> mastery challenge, explanation/Feynman, then transfer.

Its near-mastery difficulty uses IRT ability `theta` to target approximately 70% probability of success and maps that latent difficulty into a bounded runtime difficulty target.

### What to borrow

- phase-specific ranking;
- prerequisite-fringe filtering before ranking;
- deterministic audit rationales;
- expected-information-gain diagnostic selection;
- clean separation of concept selection from activity selection;
- misconception and retention overrides;
- difficulty targeted to predicted success probability;
- LLM semantic proposals behind validation boundaries.

### Caveat

Tutor MCP is relatively new/alpha and should be treated as an implementation donor, not evidence that these policies improve real learner outcomes.

## ScaffoldLM — strongest LLM step-planning reference

Paper/code:
- https://aclanthology.org/2026.acl-long.325/
- https://github.com/BNU-ERC-ITEA/ScaffoldLM

ScaffoldLM decomposes a complex problem into an ordered pedagogical plan of intermediate guiding questions and reference answers. During tutoring it explicitly assesses the learner's latest response, tracks whether the current step target is achieved, updates an assessment-driven memory, and either remediates the current step or advances.

This is a strong reference for Study OS's missing atomic episode controller:

```text
complex target
-> intermediate target 1
-> assess
-> remediate or advance
-> intermediate target 2
-> assess
-> ...
-> final reconstruction / transfer
```

Important distinction: ScaffoldLM's strength is **LLM pedagogical planning and step-state memory**, not psychometric candidate ranking or a mature product runtime.

## Oppia — strongest atomic curriculum decomposition reference

Repository/guides:
- https://github.com/oppia/oppia
- https://github.com/oppia/oppia/wiki/Lesson-Creation-Guide

Oppia's content methodology is particularly relevant to Study OS's curriculum gap.

A skill is defined as a concrete observable outcome, typically in a `Given X, do Y` form. Authors are explicitly encouraged to decompose a topic into many concrete skills, record prerequisites, and order skills from simpler to more complex. The lesson-design guide warns against introducing more than one new skill per question where possible and asks authors to account for hidden prerequisite skills.

Skill tables include:

- concrete skill;
- specific errors/misconceptions;
- remediation;
- development/explanation;
- concept/test/recap/final-challenge items;
- difficulty bands;
- prerequisite/acquired/practiced skills.

Oppia also supports prerequisite diagnostics and skill-linked question banks.

### What to borrow

- atomic observable competency definition;
- explicit prerequisite DAG;
- one-new-skill-per-item authoring discipline;
- concrete misconception definitions that predict learner responses;
- recap/final challenge structure;
- multiple equivalent items per skill;
- stable item difficulty metadata.

## OATutor — strongest research-backed KC/step/scaffold donor

Repository/content:
- https://github.com/CAHLR/OATutor
- https://github.com/CAHLR/OATutor-Content

OATutor decomposes problems into steps, maps steps to one or more knowledge components, associates BKT parameters with those KCs, and gives steps hints or interactive scaffolds. It maintains separately versioned content sources and course plans.

This is a strong donor for Study OS item specifications:

```text
problem
  -> step
     -> knowledge components
     -> answer oracle
     -> hint pathway
     -> scaffold subproblem
```

Its problem selection can use BKT-derived mastery and is configurable/A-B testable.

OATutor also provides stronger empirical grounding than most hobby LLM tutor repositories because it comes from a learning-science research program and has classroom-piloted content.

## catsim / EduCAT — strongest candidate-test ranking donors

Repositories:
- https://github.com/douglasrizzo/catsim
- https://github.com/bigdata-ustc/EduCAT

These projects solve a different problem from tutoring dialogue: **given an item bank and current ability estimate, which item should be administered next to obtain the most useful assessment evidence?**

`catsim` provides modular CAT components for initialization, item selection, ability estimation, and stopping. Its selectors include maximum Fisher information under IRT.

EduCAT provides broader research implementations across IRT/MIRT/neural cognitive diagnosis and selectors including MFI, KLI, MAAT, BECAT, BOBCAT, NCAT, D-opt, and MKLI.

### What to borrow now

For early Study OS, prefer interpretable candidate ranking such as:

- prerequisite eligibility;
- predicted success/ZPD fit;
- expected BKT/IRT information gain;
- item exposure/diversity penalties.

Do not immediately import neural selection policies trained on large educational datasets into an N=1 system.

## BOBCAT/BECAT — later learned item-selection policies

BOBCAT learns a question-selection policy through bilevel optimization and is useful evidence that item selection itself can become data-driven. BECAT targets efficient ability estimation through subset selection.

These are later-stage research references, not immediate Study OS dependencies. They need substantially more repeated learner/item data than Study OS currently has.

## DeepTutor — mature LLM/agent shell, weaker representation-policy donor

Repository: https://github.com/HKUDS/DeepTutor

DeepTutor is valuable because it is a much more mature agent-native tutoring application than most research prototypes. Recent Guided Learning releases use a hard per-type mastery gate and a learning dashboard, while the broader platform includes memory, RAG, visualization, agents, and restart-safe conversational infrastructure.

Use it as a reference for:

- objective/mastery workflow UX;
- agent loop/plugin architecture;
- memory surfaces;
- question-bank integration;
- model capability gating.

Do not treat it as the strongest source for evidence-driven representation switching. Its visualization/multimodal features are substantial, but representation-effect measurement and adaptive representation selection are not the same thing.

## PedagogicalRL / MathTutorBench — tutor behavior, not learner state

Repositories:
- https://github.com/eth-lre/PedagogicalRL
- https://github.com/eth-lre/mathtutorbench

PedagogicalRL trains open models to behave more like tutors than answerers using simulated multi-turn student/tutor interactions and judge-based rewards for pedagogical constraints such as scaffolding and withholding solutions.

MathTutorBench evaluates open-ended tutor skills such as Socratic questioning, mistake location/correction, and scaffolding.

Study OS should borrow these ideas primarily for **regression/evaluation of the LLM tutor behavior**, independent of the learner-state controller.

## Google Learn Your Way — strongest representation efficacy benchmark, not OSS

Research:
- https://research.google/blog/learn-your-way-reimagining-textbooks-with-generative-ai/
- https://doi.org/10.3389/frai.2026.1783117

Learn Your Way transforms grounded source content into multiple representations including immersive text, quizzes, narrated slides, audio, and mind maps. It also re-levels source text by selected grade and personalizes examples while trying to preserve source scope.

A 2026 experimental study with 60 students reported stronger immediate and delayed performance than a digital-textbook control. This makes it an important representation-learning research benchmark.

However, its published approach emphasizes learner choice among representations and grade/interest personalization more than **automatic evidence-driven selection of which representation is best for a specific learner-state bottleneck**. Study OS's representation intervention/outcome model should therefore remain its own research layer rather than copying a fixed modality preference model.

## Recommended Study OS synthesis

### 1. Curriculum graph

Borrow Oppia/OATutor principles:

```text
competency
  id
  observable behavior
  prerequisites[]
  misconception taxonomy[]
  task modes[]
  transfer targets[]
```

Problems should decompose into steps, and steps should map to one or more competencies/KCs.

### 2. Complexity is a vector, not one level

Keep the current L0-L10 task ladder, but augment item metadata with independent dimensions such as:

- concept depth;
- prerequisite distance/count;
- number of simultaneously maintained state variables;
- control-flow complexity;
- representation/translation distance;
- surface novelty;
- scaffold/assistance level;
- implementation load;
- algorithmic time/space tradeoff demand;
- transfer distance.

A single `difficulty=7` is insufficient to distinguish why an item is difficult.

### 3. Candidate generation then ranking

Do not ask the LLM to choose freely from the full curriculum.

First create a deterministic candidate set:

- prerequisites satisfied;
- compatible with current phase;
- valid item exposure state;
- required hidden/transfer constraints preserved.

Then rank candidates. A reasonable initial synthesis, to be tested rather than treated as truth, is:

```text
candidate_score(item) =
    w_info      * expected_information_gain
  + w_zpd       * predicted_success_fit
  + w_goal      * goal_relevance
  + w_retention * retention_urgency
  + w_transfer  * transfer_value
  + w_error     * misconception_discrimination_value
  - w_repeat    * recent_exposure_penalty
  - w_load      * predicted_overload_risk
```

`eligible(item)` remains a hard gate rather than just another weighted feature.

Each score component and chosen candidate should be auditable.

### 4. Separate assessment ranking from teaching ranking

During **diagnostic assessment**, maximize information and discrimination.

During **instruction**, maximize learning value under prerequisite/ZPD constraints.

During **maintenance**, prioritize retention urgency and transfer.

These objectives should not be collapsed into one permanent formula.

### 5. LLM responsibilities

The LLM should be strongest where generative flexibility is useful:

- propose goal-to-concept relevance;
- generate/translate representations;
- produce Socratic prompts and examples;
- explain errors after attempts;
- propose misconception hypotheses;
- generate candidate variants from a constrained item spec;
- assess open-ended explanations when no deterministic grader exists, with provenance and uncertainty.

The deterministic Study OS core should own:

- canonical evidence;
- prerequisite eligibility;
- task/item identity and exposure;
- assistance ceilings/fading rules;
- advancement gates;
- candidate scoring inputs;
- retention schedule;
- checkpoint derivation;
- deterministic graders where possible.

### 6. Representation engine remains Study OS-specific

A representation should be modeled as an intervention, not as a learner personality label.

For each representation switch record:

```text
learner state before
bottleneck hypothesis
representation family/version
learning operation
assistance level
immediate outcome
outcome after fading
transfer outcome
delayed outcome
self-report
```

Over time derive contextual effects such as `state_trace + predict` helping invariant-to-control-flow translation under a specific prerequisite state. Do not infer a fixed "visual learner" profile.

## Revised P2 research order

Before implementing the original P2A-P2E roadmap, insert an OSS donor/reproduction gate:

### P2-OSS0 — reproduce donor mechanisms offline

Implement small isolated adapters/tests for:

1. Tutor MCP-style prerequisite-fringe + phase-specific concept ranking.
2. catsim-style information-based item selection on a synthetic Study OS item bank.
3. Oppia/OATutor-style competency/step/KC representation for one real Python/DSA slice.
4. ScaffoldLM-style stepwise plan on one complex DSA problem.
5. Study OS representation intervention/outcome tracking around the same learner bottleneck.

Run all of them in shadow/offline mode against recorded or synthetic trajectories before allowing them to control the live tutor.

### Acceptance

A candidate controller must expose, for every decision:

- candidate set;
- hard exclusions and why;
- score components;
- selected item/action;
- expected evidence to be gained;
- actual learner result afterward;
- whether the policy should be revised.

Only mechanisms that improve decision quality or observability should be promoted into the live P2 runtime.

## What not to copy

- fixed visual/auditory/kinesthetic learning-style profiles;
- opaque deep knowledge tracing before sufficient repeated data exists;
- one global mastery percentage;
- LLM-only prerequisite graphs with no validation/versioning;
- reward models that become the only source of learner truth;
- giant LMS/application shells when only a small deterministic algorithm is needed;
- psychometric candidate-ranking methods whose assumptions cannot be supported by the available N=1 item data.

## Bottom line

The earlier donor shortlist was directionally useful but too coarse. Study OS should not rank one OSS project as the universal winner. It should use a **composite architecture**:

```text
Study OS evidence/provenance/checkpoints
        +
Tutor MCP-style regulation
        +
Oppia/OATutor atomic curriculum model
        +
ScaffoldLM stepwise LLM tutoring plan
        +
catsim/EduCAT assessment candidate ranking
        +
FSRS retention
        +
PedagogicalRL/MathTutorBench tutor-behavior evaluation
        +
Study OS representation-effect experiments
```

This gives Study OS a stronger path than either inventing every adaptive mechanism or replacing the existing evidence architecture with a monolithic tutor/LMS.