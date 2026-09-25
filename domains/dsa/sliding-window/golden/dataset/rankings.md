# Jev rankings — pedagogy golden dataset v0.1

Model: `typesafe/jev-1.13` via OpenRouter Decisions API. Prompt version: `study-os.pedagogy-jev-rank.v1`.

Criteria (score questions): faithful_to_transcript, one_concept_only, diagram_does_not_leak_answer_on_exercise, same_representation_on_correct_and_wrong, stepwise_goal_clarity, multi_representation_moat_fit.

Spend: **$0.001824** across 38 calls, 43440 input tokens (output free on Jev).

## Teaching moves

| rank | id | rank_key | notes |
|---:|---|---:|---|
| 1 | `move.enumerate` | 0.9446 | Learner returns (i, num) pair for a given value under enumerate(a) |
| 2 | `move.box_size_k` | 0.9329 | Learner lists the numbers inside the box for a given k (do not move box with i yet) |
| 3 | `move.window_sum` | 0.925 | Learner computes sum[i] as sum of box starting at i; partial (contents only) → ask arithme |
| 4 | `move.successive_sums` | 0.9246 | Learner finds sum[i+1], sum[i+2], ... one window at a time on the same box chart |
| 5 | `move.box_start_i` | 0.9237 | Learner identifies box contents when i is the start index and k is length |
| 6 | `move.position.intro_then_exercise` | 0.9179 | Learner names position(p) of a given number (1-based) |
| 7 | `move.recurrence_repetition` | 0.9175 | Learner sees same formula with new i each turn (bridge to loop); not full Python yet |
| 8 | `move.append` | 0.9092 | Learner converts S[i]=expr into S.append(expr); expression unchanged |
| 9 | `move.index.intro_then_exercise` | 0.9029 | Learner computes i = p - 1 for a number; understands index is 0-based |
| 10 | `move.problem.intro` | 0.8429 | State the problem and introduce a = numbers; get ready signal |
| 11 | `move.controller.wrong_path` | 0.7492 | On wrong: give answer, show why on same chart, reassure, different retry, verify before ad |
| 12 | `move.controller.arrow_rule` | 0.7 | Arrows/circles only for introducing or correcting; never on exercise diagrams that would r |

## Diagram variants

| rank | id | rank_key | notes |
|---:|---|---:|---|
| 1 | `diag.window_sum.exercise` | 0.8521 | No box arrows; learner computes sum[i=2] |
| 2 | `diag.box_k.exercise` | 0.8462 | State k; learner fills which numbers; no box glyph that answers |
| 3 | `diag.successive_sums.intro` | 0.8125 | Neighboring boxes; do not replace with generic formula first |
| 4 | `diag.enumerate.exercise` | 0.8058 | Omit answer-revealing pair row on exercise |
| 5 | `diag.position.exercise` | 0.7988 | Same rows; no arrows that reveal the asked position |
| 6 | `diag.index.exercise` | 0.7867 | No circles/arrows on exercise |
| 7 | `diag.box_k.intro` | 0.7808 | k = how many numbers in the box; do not move with i yet |
| 8 | `diag.window_sum.intro` | 0.7712 | Keep box visible; sum[i] = add numbers in box starting at i |
| 9 | `diag.box_start.exercise` | 0.7667 | i and k stated; no arrows marking contents |
| 10 | `diag.controller_loop` | 0.7637 | Controller flowchart for agents; not the learner's primary teaching diagram |
| 11 | `diag.enumerate.intro` | 0.7625 | Vertical pairing; exercise may omit the pair row |
| 12 | `diag.position.correct` | 0.7212 | Show why after correct or wrong |
| 13 | `diag.box_start.intro` | 0.7142 | i = where the box starts |
| 14 | `diag.index.intro` | 0.6983 | Circles group the same column; i = p - 1 |
| 15 | `diag.position.intro` | 0.6979 | Introduce position with answer cues |
| 16 | `diag.concept_tree.lesson_map` | 0.6004 | Lesson-map only for overview of the path, NOT for teaching a relation inside a step. Alex  |

## Anti-patterns (as rejection rules)

| rank | id | rank_key | notes |
|---:|---|---:|---|
| 1 | `ap.advance_after_one_correct_post_error` | 0.8375 | Advancing immediately after a single corrected answer following an error |
| 2 | `ap.exercise_with_answer_arrows` | 0.8318 | Leaving arrows/circles that reveal the answer on an exercise chart |
| 3 | `ap.mermaid_step_dump` | 0.7793 | Mermaid flowchart as the teaching diagram for a step |
| 4 | `ap.dont_use_index_to_explain_k` | 0.7668 | Using index motion to explain k before k is understood |
| 5 | `ap.index_equals_value_examples` | 0.6904 | Examples where index and value coincide (cognitive load) |
| 6 | `ap.overcomplex_sum_index` | 0.6743 | Listing many sum[i] → start at i → a+b expansions at once |
| 7 | `ap.remove_box_too_early` | 0.6693 | Removing the box representation when introducing sum[i] or validating S |
| 8 | `ap.text_wall_or_premature_formula` | 0.66 | Symbolic formula lecture before the process is seen on the chart |
| 9 | `ap.answer_leak_in_assessment` | 0.6361 | Showing the filled result when asking the learner to produce it |
| 10 | `ap.too_much_at_once` | 0.5864 | Writing more than the array / bundling asks |

## How to read scores

Each item has `jev_scores.<criterion>.score` (0-based mean level index) and `.normalized` in [0,1].
`jev_rank` is 1 = highest mean normalized score within its file. Confidence is distribution peakedness, not correctness — agents must still eval against transcript citations.
