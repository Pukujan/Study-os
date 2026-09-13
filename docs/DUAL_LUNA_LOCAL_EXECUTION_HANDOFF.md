# Local Luna handoff — one-command dual-Luna transcript

Status: **immediate local execution task for PR #77**

## Objective

Produce the raw evidence first:

```text
local Luna student
    ↓
local Luna teacher using the real Study OS MCP path
    ↓
14 DSA problems × 15 exchanges
    ↓
210 learner messages + 210 teacher responses
    ↓
raw JSONL + Markdown transcript
```

No pedagogical grading, repair, redesign, or dataset comparison happens during generation.

## Run it

From the local Study-os checkout on this branch:

```bash
python tools/run_dual_luna_local_codex.py
```

That one command now handles the testing plumbing itself. It:

1. verifies local Codex CLI is runnable;
2. runs Study OS `doctor`, migrating and rechecking if needed;
3. replaces only the test-specific Codex MCP entry `study-os-local-test` so it points at this checkout's `python cli/study_os.py mcp` stdio server;
4. starts independent local Codex/Luna student and teacher sessions;
5. uses `--dangerously-bypass-approvals-and-sandbox` for this local harness so MCP calls do not pause for approval;
6. requires a completed `study-os-local-test` MCP tool call on every teacher turn, so a free-form teacher answer cannot silently enter the transcript;
7. stores the full current-problem conversation in every turn payload, so a stale/broken Codex resume can be replaced by a fresh local session without losing logical dialogue context;
8. writes JSONL and Markdown after every completed exchange;
9. resumes from an existing JSONL transcript automatically after interruption.

Hosted child Codex tasks, inherited child approval settings, OpenCode, and a persistent JSONL Luna daemon are not part of this path.

## Smoke only when debugging

```bash
python tools/run_dual_luna_local_codex.py \
  --fresh \
  --scenario two-sum-dictionary \
  --turns-per-problem 3 \
  --allow-short-run
```

For the real evidence run use the one-command invocation with no short-run flags. `--fresh` restarts from zero; without it, the runner continues from the transcript already on disk.

## Outputs

```text
artifacts/dual-luna-dsa-transcript.jsonl
artifacts/dual-luna-dsa-transcript.md
```

The transcript contains the problem, coarse learner-signal provenance, learner message, and learner-visible Study OS teacher response. It intentionally contains no score, violation list, expected answer, pass/fail verdict, or automatic repair.

## Important behavior

The student receives only the problem, live conversation, and coarse behavioral signal (`clarification`, `wrong_or_uncertain`, `recovery_or_check`). It never receives the corpus answer key.

The teacher is required to use Study OS. If Study OS says a problem is unknown or needs compilation, that real behavior belongs in the transcript; the teacher must not hide the gap by inventing a lesson.

## Stop condition

The immediate task is complete when the 210-exchange raw transcript exists. Bring that artifact back for analysis before deciding what to change in prompts, constrained model generation, decomposition, canonical assets, or controller behavior.
