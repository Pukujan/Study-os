# TASK-SOS-0010 — Extract pedagogy golden dataset + agent skill from transcript

<!-- continuity:task {"acceptance":["Structured dataset under domains/dsa/sliding-window/golden/dataset/ includes manifest.json, moves.jsonl, diagrams.json, anti_patterns.json, representation_playbook.md, moat.md, rankings.md with Jev scores","docs/pedagogy/SKILL-golden-tutor.md exists with when-to-use description and a copy-paste repeated tutor system prompt","Extraction receipt on issue #111 lists turn/diagram/anti-pattern counts and sample transcript citations","Draft PR Refs #111 only; no UI redesign / SOS-0005 work mixed in","Hosted Jev (typesafe/jev-1.13) rankings recorded with spend"],"depends_on":[],"goal":"Stop treating the short golden markdown files as sufficient. Extract durable, machine-readable golden teaching data from the long sliding-window pedagogy calibration transcript (~16k lines), plus a reusable agent skill and a repeated tutor system prompt that every agent can read and copy.","id":"SOS-0010","issue_url":"https://github.com/Pukujan/Study-os/issues/111","next_action":"Open draft PR, post extraction receipt on #111, wait for Alex review. Do not merge UI redesign work.","owner":"Pukujan (GitHub assignee); primary writer: Grok Bot executor on task/SOS-0010-pedagogy-golden-dataset","priority":"P1","protocol_version":"0.1.0-draft","schema":"project-continuity.task.v1","status":"in_progress","why":"Alex's real teaching pattern lives in the long transcript (ASCII box/index diagrams, stepwise goals, representation switches, corrections when diagrams/mermaid/text walls went wrong). Short goldens alone under-specify this. Agents keep assuming the short files are enough."} -->

- Status: in_progress
- Owner: Pukujan (GitHub assignee)
- Priority: P1
- Depends on: none (builds on SOS-0002 goldens + 2026-09-04 transcript)
- Branch: `task/SOS-0010-pedagogy-golden-dataset`
- GitHub issue (leaf): #111 — parent: #82 (web app epic) — related: #101 (SOS-0005), #80 (SOS-0002), #92 (agent-vs-agent eval)

## Goal

Extract durable, machine-readable golden teaching data from the long sliding-window pedagogy calibration transcript, plus a reusable agent skill and repeated tutor system prompt.

## Why

Short golden markdown files under-specify the real teaching pattern. The long transcript (~16k lines) holds ASCII diagram variants, arrow rules, wrong-path repair, anti-patterns Alex rejected, and the multi-representation moat.

## Deliverables

1. `domains/dsa/sliding-window/golden/dataset/` — manifest, moves.jsonl, diagrams.json, anti_patterns.json, representation_playbook.md, moat.md, rankings.md (Jev-scored)
2. `docs/pedagogy/SKILL-golden-tutor.md` (+ workflows copy)
3. Receipt comment on #111
4. Draft PR Refs #111 only

## Out of scope

- SOS-0005 lesson player / UI redesign
- Merging to main without review
- Replacing the existing short golden fixtures (they remain; dataset complements them)

## Acceptance criteria

- [x] Dataset files with source hashes and transcript citations
- [x] Jev rankings + spend recorded
- [x] Skill with repeated prompt
- [ ] Draft PR open (Refs #111)
- [ ] Receipt on #111
