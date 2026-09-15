# Decomposition reliability qualification v1

Status: **implemented bounded orchestration; no qualification claim yet**.

This is the execution contract for the next model-tutoring phase. A single
passing run, or a collection of runs made with different prompts, is not a
qualification result.

## Frozen-candidate epoch

The same candidate must produce every public batch in one epoch. The candidate
fingerprint records:

- checked-out code revision (including tracked working-tree changes);
- decomposition, diagnosis, and generation prompt versions and SHA-256 hashes;
- teaching-plan and turn-trace schema versions;
- decomposer skill, checklist, and evaluation-policy hashes; and
- model identifier.

If any component changes, the current evidence is closed as historical and a
new candidate/epoch starts at public batch zero. Evidence is never silently
mixed across candidates.

## Public and hidden gates

The public corpus is partitioned by a seeded shuffle into non-overlapping
batches (four problems by default). Each batch runs through the existing generic
Luna → schema → deterministic controller → acceptance path. A public epoch is
complete only after every public problem has passed its own acceptance gate.

`PUBLIC_EPOCH_PASSED` is deliberately not the terminal product status. Hidden
promotion scenarios must be supplied by an external command that does not leak
their oracle to the teacher. Only a passing hidden promotion epoch may produce
`DECOMPOSITION_RELIABILITY_QUALIFIED`.

## Bounds and resume

`tools/run_model_tutoring_autonomous_loop.py` checkpoints a JSON ledger before
and after every batch. It has explicit limits for candidate generations, model
calls, and optional wall-clock runtime. On interruption, invoke it again with
`--resume`; it resumes the next missing batch and reuses an incomplete batch's
own runner checkpoint. A failed batch stops the invocation unless a bounded
`--repair-command` is supplied. The repair hook must change the candidate
fingerprint before another epoch is started; an unchanged repair is recorded
and cannot loop forever.

The planning-only command is safe for repository checks:

```bash
python tools/run_model_tutoring_autonomous_loop.py \
  --goal decomposition-reliability-qualified \
  --batch-size 4 \
  --max-candidates 10 \
  --max-model-calls 5000 \
  --dry-run
```

The real local run omits `--dry-run` and uses `--resume` after an interruption.
The default batch executor invokes `tools/run_model_tutoring_all_dsa.py` and
`tools/check_model_tutoring_all_dsa.py` with the selected scenario IDs. Hidden
promotion is intentionally an explicit integration point; absent a hidden
fixture/evaluator the ledger remains `PUBLIC_EPOCH_PASSED`.

## Authority boundary

Luna may propose decomposition, diagnosis, and learner-facing teaching. The
schema and deterministic controller still own progression, assistance ceilings,
variable/representation contracts, completion evidence, and provenance. The
qualification ledger only records whether independent acceptance passed; it
does not rewrite transcripts or convert replay evidence into learner mastery.

## Required evidence before promotion

For each frozen candidate, retain the ledger, generated plans, raw transcripts,
traces, acceptance reports, prompt-evaluation receipt, and targeted
TDD/differential/metamorphic/property/mutation results. A future hidden run
must add its own redacted report without exposing private problem statements or
answers to the measured teacher.
