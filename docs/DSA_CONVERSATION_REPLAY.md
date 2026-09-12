# DSA conversation replay harness

This is a learner-visible regression harness, not another tutoring controller.

Its job is to answer one question:

> When a realistic learner talks to the normal Study OS/Luna path, does the visible tutoring stay on the right concept, preserve the calibrated representation, use the expected variables, repair mistakes locally, and keep the interaction small enough to follow?

## Corpus

`datasets/dsa-conversation-replay.v0.1.json` contains more than the requested minimum:

- 14 DSA problems;
- 210 learner turns;
- 210 expected assistant replies during a full run;
- therefore 420 visible learner/assistant messages in one complete replay;
- realistic clarification, wrong/uncertain, and recovery/check turns for every problem.

Problems include Two Sum, Contains Duplicate, Best Time to Buy and Sell Stock, Valid Parentheses, Binary Search, Reverse Linked List, Merge Two Sorted Lists, Maximum Depth of Binary Tree, BFS Shortest Path, Number of Islands, Kth Largest Element, Sliding Window Maximum Sum, Merge Intervals, and Valid Palindrome.

The learner text is intentionally informal. It includes confusion, wrong directions, shorthand, requests to slow down, requests for charts, variable-name objections, and later recovery.

## Two lanes

### Lane A — realistic back-and-forth

Run the entire corpus through the actual local actor:

```bash
python3 tools/replay_dsa_conversations.py run \
  --actor-cmd "python3 tools/replay_opencode_adapter.py" \
  --report artifacts/luna-dsa-replay.json
```

The checked-in adapter is intentionally harness-only. It creates one
headless OpenCode HTTP session per scenario with `agent: luna`, seeds an
isolated Study OS PIR run, then sends one bounded prompt per learner turn.
It reads optional overrides from `STUDY_OS_REPLAY_AGENT`,
`STUDY_OS_REPLAY_OPENCODE_URL`, `STUDY_OS_REPLAY_MCP_URL`, and
`STUDY_OS_REPLAY_TIMEOUT`; it contains no machine-specific paths or
credentials. The headless server must expose the local Study OS MCP entry and
be reachable at the configured URLs. Set
`STUDY_OS_REPLAY_ACTOR_CMD` to the same command to opt into the connected
regression test; ordinary CI skips that test because it cannot provide a live
Study OS/MCP session.

The actor command stays alive for the whole run and speaks JSONL over stdin/stdout.

Each input line looks like:

```json
{
  "type": "study_os_replay_turn",
  "scenario_id": "two-sum-dictionary",
  "title": "Two Sum",
  "problem": "Given nums and target, return indices of two numbers whose sum is target.",
  "variables": ["nums", "target", "box", "i", "num", "needed"],
  "visual_family": "index-value-box",
  "stage": "needed",
  "turn_index": 4,
  "learner_message": "i think needed is num-target? 3-9=-6",
  "history": []
}
```

The adapter must return one JSON line:

```json
{"assistant_message":"...exact learner-visible reply..."}
```

or a JSON string containing the reply.

The adapter should exercise the **normal Study OS learner-facing path**. Do not bypass Study OS and directly prompt Luna if the purpose of the run is to validate the product.

The hidden expected assertions are deliberately not sent to the actor.

### Lane B — independent visible-output grading

The same checker can grade a transcript captured by any route:

```bash
python3 tools/replay_dsa_conversations.py grade \
  --transcript artifacts/luna-visible-turns.jsonl \
  --report artifacts/luna-visible-grade.json
```

Each transcript line needs:

```json
{
  "scenario_id": "binary-search",
  "turn_index": 7,
  "assistant_message": "...visible reply..."
}
```

This lane lets the visible conversation be captured first and judged afterward. The tutor does not get the rubric.

## What the checker currently rejects

The checker intentionally targets the failure classes repeatedly seen in the saved Study OS calibration sessions:

- `WRONG_DIRECTION`: the response does not contain any anchor for the current learner-sized concept;
- `FUTURE_OR_RENAMED_CONCEPT`: the response jumps ahead or introduces a forbidden alias such as `seen` when the scenario requires `box`;
- `REPRESENTATION_DROPPED`: a chart/trace is required but the visible response becomes detached prose;
- `OUTPUT_BUDGET_EXCEEDED`: the response turns into a wall of text;
- `BACK_AND_FORTH_DROPPED`: the turn should end with a small learner check but does not.

The report names the **first visible divergence** and includes every failed turn.

This is intentionally a coarse deterministic gate. It should become stricter only when a real failed conversation proves another visible invariant is necessary.

## Corpus validation

```bash
python3 tools/replay_dsa_conversations.py validate
```

Expected current output:

```text
valid: 14 problems / 210 learner turns
```

The unit tests also enforce the minimum corpus size and verify that the actor payload cannot see the hidden answer key:

```bash
PYTHONPATH=src python3 -m unittest tests.test_dsa_conversation_replay -v
```

## Development rule

Do not respond to a failed replay by adding a new architecture layer first.

Use the report in this order:

```text
first divergent learner-visible turn
        ↓
identify the smallest visible invariant that failed
        ↓
fix that response path / lesson asset / prompt boundary
        ↓
rerun the same conversation
        ↓
only generalize after the replay passes
```

A green controller test is not a substitute for a green learner-visible replay.

A green replay is also not a mastery claim. It only establishes that Study OS produced the expected teaching behavior under these scripted conversations.
