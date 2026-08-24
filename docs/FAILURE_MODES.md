# Failure Modes and Bridges

This document is intentionally adversarial. A Study OS experiment is not considered useful because it feels personalized or produces attractive visualizations. It must survive the failure modes below.

## A. Learning-validity failures

### F01 — Self-reported understanding is mistaken for mastery
**Failure:** learner says “I get it,” system records success.

**Bridge:** preserve self-report separately; require behavioral evidence through prediction, explanation, reconstruction, implementation, transfer, or delayed retention.

### F02 — Immediate fluency is mistaken for durable learning
**Failure:** explanation feels clear while visible, but cannot be reconstructed later.

**Bridge:** delayed retrieval checks; spaced review; no-reference reconstruction.

### F03 — Problem familiarity masquerades as transfer
**Failure:** learner solves a near-copy of a practiced problem.

**Bridge:** hidden transfer set with changed surface form and controlled overlap; record novelty level.

### F04 — Hint dependence is hidden
**Failure:** learner gets correct answers only because the tutor keeps supplying structure.

**Bridge:** count hint level and representation support; explicitly fade assistance; assess blank implementation.

### F05 — Practice effects contaminate experimental comparisons
**Failure:** representation B looks better because it came second.

**Bridge:** matched problem variants, alternating-treatment designs where feasible, repeated baselines, counterbalanced ordering when enough equivalent problems exist.

### F06 — Fatigue, frustration, time of day, or motivation confounds outcomes
**Failure:** poor performance is labeled as a representation problem.

**Bridge:** lightweight session context (duration, perceived fatigue/frustration, interruption); do not infer cognitive cause from one failed attempt.

### F07 — Novelty/Hawthorne effects
**Failure:** a new visualization initially increases engagement but not learning.

**Bridge:** repeated exposure and delayed measures; track engagement separately from mastery.

## B. Representation failures

### F08 — “Visual learner” becomes a fixed identity
**Failure:** system overfits instruction to a presumed sensory learning style.

**Bridge:** never encode fixed visual/auditory learner types. Select representations from observed task performance and change them when evidence changes.

### F09 — Representation overload
**Failure:** prose + flowchart + animation + code + narration simultaneously increases extraneous load.

**Bridge:** minimum necessary representation set; progressive disclosure; track concurrent representations and learner-reported overload.

### F10 — Attractive visualization is semantically wrong
**Failure:** animation, Mermaid diagram, or generated image disagrees with the algorithm.

**Bridge:** deterministic state models for authoritative DSA visuals; executable reference implementations; representation-version tests; generated media is non-authoritative unless derived from validated state.

### F11 — Representation changes content as well as modality
**Failure:** comparing a diagram and prose also changes the explanation, so causal interpretation is impossible.

**Bridge:** canonical Lesson IR; record both representation family and representation operation; controlled experiments should hold semantic content constant when possible.

### F12 — Too many representations create an unsearchable content library
**Failure:** project becomes a multimedia course rather than a learning system.

**Bridge:** representations are generated/selected from a canonical lesson structure; keep only versions with provenance and evaluation relevance.

## C. AI-specific failures

### F13 — AI gives the solution before learning occurs
**Failure:** helpfulness destroys productive struggle.

**Bridge:** tutor policy with staged assistance: ask/predict -> small cue -> structural hint -> partial scaffold -> solution only after explicit threshold or request.

### F14 — AI hallucinates DSA facts, invariants, complexity, or code
**Failure:** learner internalizes incorrect material.

**Bridge:** canonical reference solution, executable tests, complexity assertions where practical, source-grounded lesson knowledge, deterministic evaluator for code behavior.

### F15 — AI-generated code creates dependency
**Failure:** learner can assemble working projects but cannot explain or repair generated code.

**Bridge:** code-reading, tracing, debugging, blank-editor checkpoints, and “explain this generated code” assessments. AI-off phases are a feature, not a punishment.

### F16 — Tutor infers an incorrect learner state
**Failure:** LLM labels “invariant confusion” when the learner actually has a Python syntax gap.

**Bridge:** derived labels require evidence IDs + confidence; maintain multiple hypotheses; test diagnosis through targeted probe questions before committing intervention.

### F17 — LLM judge rewards its own style or answer
**Failure:** evaluation becomes circular.

**Bridge:** deterministic tests first; explicit rubrics second; independent model/human review for subjective outputs; keep evaluator identity/version; hidden expected properties unavailable to intervention model where possible.

### F18 — Model drift destroys longitudinal comparability
**Failure:** model/provider update changes tutor behavior mid-study.

**Bridge:** log provider/model/prompt/lesson/representation versions; maintain fixed benchmark sessions or frozen eval prompts; treat model changes as experimental interventions.

## D. N=1 research failures

### F19 — Subject 001 is treated as a population
**Failure:** personal findings become universal pedagogical claims.

**Bridge:** evidence lifecycle: `subject observation -> replicated subject finding -> lesson hypothesis -> multi-subject finding`. CI/docs must prohibit silent promotion.

### F20 — Introspection is overtrusted
**Failure:** articulate learner explanations are treated as causal proof.

**Bridge:** self-report is high-value evidence but remains self-report. Compare it against behavior and delayed outcomes.

### F21 — Too few repetitions to distinguish noise from intervention effects
**Failure:** one breakthrough becomes a product feature.

**Bridge:** repeated measures, alternating interventions, replication across problems and sessions.

### F22 — The learner becomes optimized for the test suite
**Failure:** Subject 001 memorizes benchmark problems or interaction patterns.

**Bridge:** rotating hidden transfer forms; generate new variants from validated concept constraints; keep holdouts inaccessible to tutor when feasible.

### F23 — Research overhead harms the actual learner
**Failure:** constant surveys/logging interrupts studying and causes burnout.

**Bridge:** capture evidence automatically; ask only high-information questions; set session research-overhead budget; learning outcome outranks telemetry completeness.

## E. Data and privacy failures

### F24 — Private transcript data is committed to the public repository
**Failure:** sensitive conversations become permanent public Git history.

**Bridge:** raw transcript evidence defaults to local/private storage; public repo stores hashes, schemas, redacted examples, aggregate/curated findings. `.gitignore` blocks session raw evidence.

### F25 — Raw and derived data are mixed
**Failure:** later agents cannot distinguish what the learner actually said from an AI interpretation.

**Bridge:** immutable raw artifacts; normalized transcript derived separately; evidence classes `observed`, `self_reported`, `derived`.

### F26 — Schema evolution breaks old sessions
**Failure:** learning data becomes unreadable as the project evolves.

**Bridge:** version every canonical schema; never rewrite raw evidence; migrations create new derived versions; retain migration tests.

## F. Software/system failures

### F27 — Agent-driven repository drift
**Failure:** agents add features while silently changing research assumptions.

**Bridge:** root `AGENTS.md`, `PROJECT_MANIFEST.yaml`, `docs/HANDOFF.md`, explicit decision log, CI validation, and build gate. Agents must update handoff/manifest when requirements change.

### F28 — No reproducible environment
**Failure:** ingestion/evaluation works only on one machine.

**Bridge:** pinned Python tooling, CI on every PR/push, schema checks, unit tests, deterministic reference fixtures.

### F29 — CI checks software syntax but not research integrity
**Failure:** code passes while dataset provenance or evidence-class rules are violated.

**Bridge:** add research-integrity linting: prohibited raw public transcripts, required schema versions, evidence provenance, no `derived` event without derivation metadata.

### F30 — Premature deployment/CD
**Failure:** time goes into hosting/UI before learning loop is validated.

**Bridge:** CI now; CD deliberately deferred. First deployment gate requires one complete learning trajectory with immediate, transfer, and delayed evidence.

## G. Product/scope failures

### F31 — Scope explosion into every DSA concept and modality
**Failure:** video, audio, image generation, graph databases, and full curriculum arrive before the core experiment works.

**Bridge:** one learner, Python, Sliding Window, limited representations until research gate passes.

### F32 — Study OS becomes another answer generator
**Failure:** fastest route to correct code dominates UX.

**Bridge:** optimize for unaided capability and transfer, not task completion time alone.

### F33 — Study OS becomes another static course
**Failure:** curated lessons replace adaptive observation.

**Bridge:** core object remains a learning episode and representation transition, not a chapter/video.

### F34 — Study OS becomes a research database that is unpleasant to use
**Failure:** scientifically interesting logging reduces motivation to study.

**Bridge:** learner UX is primary; instrumentation must be mostly invisible and removable.

## Required metrics

Never report a single “mastery score” alone. Minimum dimensions:

- recognition;
- mental model/explanation;
- state prediction/tracing;
- invariant/reasoning;
- pseudocode/procedure;
- implementation;
- debugging;
- transfer;
- delayed retention;
- assistance/hint dependence;
- time/effort separately from correctness.

## Build gate

Do not expand the product surface until we can demonstrate one complete trajectory in Sliding Window:

1. baseline failure identified;
2. diagnosis recorded as hypothesis;
3. intervention version recorded;
4. immediate behavioral improvement measured;
5. assistance removed;
6. changed-surface transfer tested;
7. delayed retrieval tested;
8. raw/self-report/derived evidence remain separable;
9. another agent can reconstruct the experiment from repo metadata without chat history.