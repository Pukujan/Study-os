# PDD: UX defect exploration (Jev Ultrafast + Playwright)

Status: accepted product truth for guest-facing UX exploration  
Parent: #126  
Date: 2026-09-27  
Schema: `docs/schemas/ux-defect-report.v1.json`

## 1. Goal

Define (a) how guest-facing Study-os controls MUST behave, and (b) a shared defect-report contract so Jev Ultrafast exploratory runs and Playwright deterministic specs produce **comparable catch-rate** artifacts.

## 2. Expected component behavior (product truth)

| Component | SHOULD |
| --- | --- |
| Home / lanes / Start-Resume | Guest home shows subject **lanes** with Start (new) and Resume (existing session). Primary CTA is lane Start/Resume -- **not** a classic DSA PIR primary. |
| Lesson player shell | `/play/{id}` renders teach **or** probe phase with visible step content (title/body/controls). Never an empty lavender shell. |
| Explain again | Chip/control re-renders current step explanation (same step_id); DOM text or presentation version changes within 3s; does not navigate away. |
| Worked example | Chip opens worked-example card with readable `md`/`steps`; does **not** unmount React root or blank the page. |
| Companion chips | Visible, labeled, keyboard-focusable; each click yields observable panel/DOM change within 3s. |
| Back / exit to menu | Leaves `/play/{id}` for home/menu; never leaves a permanent blank `/play/{id}` without ErrorBoundary recovery. |
| Mic / speaker | Affordances visible when voice enabled; disabled/muted state is labeled; click toggles state indicator within 3s. |
| Study-buddy chat ack | Sending a chat message shows an ack (pending/sent/error) or assistant reply region update within 3s; no silent drop. |
| Review 1-5 + Submit | Panel exposes scores 1-5, why text, Submit; Submit shows submitted receipt; not like/dislike-only. |
| Number-line / growth table / arrows | Visuals readable (labels/ticks/arrows not clipped or zero-contrast); arrow affordances advance/revisit without blanking. |
| ErrorBoundary / no blank play | Any render throw shows Retry / Go home; Resume of same session shows content **or** bounded error UI -- never permanent blank play. |

## 3. Pass/fail rule (universal)

**Click -> observable change within 3s**, else defect.

Observable = URL change **or** DOM text change **or** panel/region appearance/disappearance (testid or role+name). Timeout without change => severity >= P1; blank root / uncaught throw => **P0**.

## 4. Agent output contract (Jev Ultrafast)

### Native Ultrafast output (NOT a defect report)

Ultrafast natively emits run **state**: `decisions[]`, `history[]`, `status`, page `url`/`title`, operation/target probabilities. That alone is **not** a UX defect report.

### Harness-required artifacts (WE write on top)

| Artifact | Role |
| --- | --- |
| `actions.jsonl` | One JSON object per action (timestamp, target, op, result). |
| `decisions.jsonl` | One JSON object per Ultrafast decision (aligned to native `decisions[]`). |
| `report.md` | Human summary; **must** include a `## Defects` section listing each defect id + one-line expected vs actual. |
| `summary.json` | Machine summary conforming to `ux-defect-report.v1` (this PDD's schema). |

Playwright deterministic arm writes the **same** `summary.json` shape (and may omit Ultrafast-only jsonl when N/A, but must still emit `summary.json` + `report.md` with `## Defects`).

## 5. Defect object fields

Required on each defect in `summary.json.defects[]`:

| Field | Type / notes |
| --- | --- |
| `id` | Stable string, e.g. `UX-A18-001` |
| `severity` | `P0` \| `P1` \| `P2` |
| `component` | One of the section 2 names (or short slug) |
| `control_label` | Visible label / aria-name / testid of control clicked |
| `url` | Page URL at failure |
| `expected` | Product-truth sentence from section 2 |
| `actual` | What happened (incl. "no change in 3s") |
| `repro_steps` | Ordered string[] |
| `evidence` | `{ "screenshot"?: path, "action_id"?: string }` |
| `source` | `jev` \| `playwright` |
| `related_issue_slice` | Optional `A12`..`A24` |

## 6. Compare arms

Same schema for:

1. **Ultrafast exploratory** (`source: jev`) -- open-ended guest flows.
2. **Playwright deterministic** (`source: playwright`) -- scripted clicks on the same controls.

Catch-rate = `#defects found / #controls exercised` under identical section 3 oracle, so arms are comparable.

## 7. Non-goals

- No production UI for an agent task board.
- No claiming learner mastery from exploration runs.
- Ultrafast native state files are inputs to the harness, not substitutes for `summary.json`.

## 8. Done-when (this doc ship)

- [x] This PDD under `docs/PDD_UX_DEFECT_EXPLORATION.md`
- [x] Schema at `docs/schemas/ux-defect-report.v1.json`
- Follow-on: harness writes artifacts; local `gate_ux_defect_report.py` fails on any P0/P1; CI Playwright locks controls.

## 9. Local Ultrafast vs CI (Alex clarification)

| Arm | Where it runs | Required for FE claim? |
| --- | --- | --- |
| **Ultrafast exploratory** (`source: jev`) | **Local / scout only** (Teresa-Pujan or agent box with `JEV_ULTRAFAST_ROOT`) | **Yes — FIRST** before claiming FE done |
| **Playwright deterministic + vision** (`source: playwright`) | Local and **GitHub Actions** job `playwright` | Yes — after Ultrafast; CI stays this arm only |

Ultrafast is **not** a required Actions job. Do not add Ultrafast crawl workflows to CI. Ultrafast is reliable; OpenRouter Decisions misconfig ≠ Ultrafast flake. Any P0/P1 fails the agent claim regardless of confidence (`tools/gate_ux_defect_report.py`).

