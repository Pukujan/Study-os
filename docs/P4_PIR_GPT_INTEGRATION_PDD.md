# P4/PIR Product Design — Study OS GPT Canonical PIR Integration

Date: 2026-09-05
Status: proposed implementation design
Tracker: #66
Parents: #63, #65

## Product objective

Make the existing Study OS GPT the first real learner-facing runtime for the canonical Pedagogical IR work without returning curriculum authority to the LLM.

The first release slice must let a learner open the existing Study OS GPT, present the known September-4 sliding-window problem, and traverse a pinned canonical PIR through the existing Study OS MCP.

## Product thesis

Study OS should use ChatGPT continuously for conversation and semantic interpretation while deterministic Study OS code/state owns the learning program.

```text
learner
  ↓
Study OS GPT
  ↓ semantic MCP operation
Study OS application boundary
  ↓
pinned CanonicalProblemPIR
  ↓
deterministic traversal + assessment
  ↓
renderer-safe TeachingTurn
  ↓
Study OS GPT displays/continues conversation
```

The GPT is present throughout the experience. It is not the authority for canonical graph identity, legal next transitions, deterministic assessment truth, answer exposure, or mastery.

## First-slice user experience

The user should be able to:

1. open the existing Study OS GPT;
2. paste or reference the known sliding-window max-sum problem;
3. have Study OS resolve it to a pinned canonical PIR;
4. start a problem run;
5. see the exact authorized learner-visible representation/question;
6. answer naturally;
7. receive the next authorized teaching turn;
8. ask for clarification/expansion without allowing GPT to jump ahead;
9. resume after service restart without losing problem-run state;
10. finish the historical assembled-code frontier without an unsupported mastery claim.

## Authority boundary

### Deterministic Study OS owns

- canonical problem/PIR identity and revision;
- problem-run identity;
- current canonical step;
- legal transitions;
- branch classification when deterministic assessment exists;
- PARTIAL vs INCORRECT distinction;
- required representation state;
- renderer-safe vs controller-only data separation;
- expected answers/oracles;
- advancement/blocking;
- mastery/proficiency claims;
- persistence and idempotency semantics;
- evidence provenance and module revisions.

### Study OS GPT may

- recognize user intent;
- call semantic Study OS tools;
- interpret free-language clarification requests;
- propose bounded semantic interpretations when the backend requests them;
- converse around backend-authorized teaching state;
- later propose new canonical PIR candidates for unseen problems through a separate validated compiler path.

### Study OS GPT may not

- silently skip canonical steps;
- invent an alternate teaching route while a problem run is active;
- expose controller-only expected answers;
- rewrite a frozen/parameterized chart or variable role;
- reinterpret PARTIAL as failure or success for convenience;
- infer mastery from self-report, fatigue, lesson completion, or code exposure;
- mutate canonical problem structure based on a single learner interaction.

## First-slice scope

Build now:

- known-problem resolution for the September-4 sliding-window case;
- pinned canonical PIR asset identity;
- deterministic problem-run state;
- renderer-safe teaching-turn contract;
- deterministic response submission/transition contract;
- bounded expansion request contract;
- application/MCP projection through the existing semantic boundary;
- persistence sufficient for restart/resume;
- historical replay and adversarial validation;
- live GPT integration instructions;
- PAM deployment and live-validation receipts.

## Explicit non-goals

Do not build in this slice:

- arbitrary raw-problem → PIR compilation in production;
- hidden/sealed evaluator material in the runtime;
- broad DSA curriculum generation;
- new frontend;
- production auth/tenant redesign;
- new learner-profile system;
- Luna as a runtime dependency;
- broad inference-cost optimization;
- population-level efficacy claims;
- infrastructure unrelated to proving this vertical slice.

## Product invariants

1. Personalization changes the path through a canonical graph, not the graph itself.
2. A problem run pins one canonical PIR revision for its lifetime.
3. Same accepted problem-run state plus same learner outcome produces the same authorized next state.
4. Controller-only assessment data never enters renderer-safe output.
5. Required representation continuity is learner-visible, not merely an internal flag.
6. Corrections preserve already-correct learner work unless a specific invariant requires changing it.
7. PARTIAL is first-class and cannot be collapsed into INCORRECT.
8. No runtime path may infer mastery solely from reaching the final exposed solution.
9. Existing source-turn/evidence durability remains authoritative.
10. Runtime failures fail closed rather than emitting plausible-but-unauthorized teaching content.

## Representation policy

The first integration favors deterministic learner-visible Markdown/monospace generated from validated representation state.

Example shape:

```text
a = [2, 6, 4, 1, 8]
k = 3

index:   0   1   2   3   4
value:  [2] [6] [4]  1   8
         └───────┘

Which values are inside the box?
```

GPT receives this as renderer-safe output and should display it without changing the represented roles, answer exposure, or pedagogical step.

Rich widgets may replace the renderer later while preserving the same RepresentationSpec semantics.

## Known historical behaviors that must survive

At minimum:

- correct box contents without requested arithmetic → PARTIAL;
- representation restoration after detached recurrence confusion;
- successive concrete sums before recurrence abstraction;
- recurrence before loop abstraction;
- source representation preserved during transition into code;
- localized repair of max comparison / append mistakes;
- arbitrary-k and boundary bridges before the final combined loop;
- final code exposure → assembled frontier, independent mastery unproven.

## Kill/stop criteria

Do not deploy the slice to the live GPT if any of these remain true:

- existing MCP regression failures;
- controller-only answer leakage;
- inability to reproduce required historical branches;
- restart/resume changes canonical revision or legal next state;
- GPT can advance without backend authorization;
- mutation tests demonstrate required bridges/representation can be removed without detection;
- local deployment requires unreviewed schema/controller changes;
- failures are being hidden by weakening tests or rewriting fixtures.

## Success criterion

The slice succeeds when a real Study OS GPT session can be reconstructed as:

```text
pinned canonical PIR
+ persisted problem-run state
+ learner response
→ deterministic classification/authorization
→ renderer-safe learner turn
→ durable evidence
```

and the observed path satisfies the September-4 regression constraints without granting unsupported mastery.
