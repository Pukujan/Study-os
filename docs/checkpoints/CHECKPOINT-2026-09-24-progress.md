# Study-os checkpoint — 2026-09-24 (usage pause)

**Branch:** `codex/checkpoint/wip-20260924-progress`  
**Base:** `main` @ `3127eac` (includes merged PR #116 pet MIME + DSA BoxIndex)  
**Trigger:** IRE usage almost out — push WIP + stop. No secrets in this pack.

## Goal (product)

Break hard topics (start DSA) into small stepwise pedagogical goals with **multiple forms of information representation**. After help is removed, quiz whether the learner truly understood. Live at https://study.design-bakery.com (gravebuster + Cloudflare tunnel; **no Vercel**).

## Done so far (landed on `main`)

| Item | Refs | Notes |
|------|------|--------|
| First slice FastAPI + Postgres + auth + HESI + DSA + Jev | #100 / SOS-0004 | Deployed gravebuster |
| Research durable: evidence review, voice, decisions | #108 | `docs/research/` |
| Product moat recorded | #110 | multi-rep + stepwise goals |
| SOS-0011 pedagogical decomposer research + review app | #115 / #114 | `/review/decomposer` |
| SOS-0005 lesson player redesign (pet free-roam + visuals) | #102 / #101 #103 | BoxIndex, Mermaid map, companion |
| Pet webp MIME + DSA first-step visual | #116 | Static `/mascot/*.webp` must not SPA-fallback |

## Unmerged WIP on this branch

1. **Pet sprite one-shot empty frame** (`web/src/mascot/Sprite.tsx`, cherry-pick of `b4fe121` from `task/SOS-0005-pet-v2-hover`)  
   - One-shot animations (`wave` / `celebrate` / `encourage`) ended on an empty sheet slot → live looked like empty glowing oval.  
   - Fix: end on last visible frame; `steps(frames-1)` + `forwards` for non-loop.  
   - **Not yet redeployed** when checkpoint was cut (executors stopped for usage pause).

## Open PRs (do not wait)

- **#112** `task/SOS-0010-pedagogy-golden-dataset` — golden dataset + `study-os-golden-tutor` skill  
- **#109** `task/SOS-0009-voice-robustness-research` — voice research (also partly landed via #108)  
- Older drafts: #77, #75, #72, #51, #50, #49  

## Open issues (active focus)

- **#101** SOS-0005 lesson player (visuals/pet still iterating vs Alex screenshots)  
- **#103** SOS-0006 visual identity / CGM characters  
- **#111** SOS-0010 golden extract  
- **#114** / **#113** SOS-0011 decomposer (human ratings next; dropdown bug may still need verify after #116 deploy)  
- **#107** SOS-0005 research gate  
- Web epic **#82** and children #84–#98  

## Architecture decisions (binding)

- **Hosting:** all on gravebuster (`study.design-bakery.com`); Postgres 16 in Docker; Metabase private on Tailscale.  
- **Decision layer:** rules → Jev (`typesafe/jev-1.13` OpenRouter decisions) → frontier LLM only when needed.  
- **Auth:** Google primary + local email/passphrase fallback; open signup; AI spend caps.  
- **Analytics:** Postgres only (no PostHog).  
- **Pet:** chibi learner = companion; robot = rare idle visitor. Teaching charts = cheap dynamic SVG/Mermaid/KaTeX, not PNG.  
- **Workflow:** issue + `TASK-SOS-####` + `task/` branch + PR `Refs #N` (never `close #N`); CI: Validate research harness + Python 3.11.  

## Known live bugs (as of pause)

1. Alex screenshot: empty pet glow + broken DSA copy (`are learning how…`) + plain `numbers(a)` instead of BoxIndex — **partially addressed by #116** (MIME fixed live: `Content-Type: image/webp`); one-shot empty-frame fix is **this branch only**.  
2. Decomposer review dropdowns empty when `/review/decomposer/data/index.json` SPA-falls back — #116 added guards/tests; **re-verify live** after next deploy.  
3. Draft UX shots under box `/workspace/ux-shots/draft/` are **not** proof of live quality.

## Key paths

```
docs/research/README.md
docs/research/sos-0005-evidence-review.md
docs/research/pedagogical-decomposer.md
docs/research/decomposer-review/
domains/dsa/sliding-window/golden/
web/src/mascot/{Pet,Sprite}.tsx
web/public/mascot/*.webp
web/src/visuals/{BoxIndex,LessonMap}.tsx
src/study_os/web/api.py
src/study_os/web/player/lessons/sliding-window-box.v1.json
tasks/TASK-SOS-0005-lesson-player-redesign.md
tasks/TASK-SOS-0011-pedagogical-decomposer.md
```

Box worktrees (not all in git): `/workspace/study-os-ux`, `/workspace/study-os-sos0011`, `/workspace/study-os-golden-extract`, `/workspace/ux-shots/draft/`.

## Next steps (when usage resumes)

1. Merge/deploy this checkpoint (or cherry-pick Sprite fix) to gravebuster; hard-refresh; screenshot pet full-body + DSA BoxIndex first step.  
2. Confirm `/mascot/pet-idle.webp` and `/review/decomposer/data/index.json` return real assets (not SPA HTML).  
3. Merge or finish **#112** SOS-0010 goldens.  
4. Collect Alex ratings on `/review/decomposer`.  
5. Do **not** treat draft shots as live; verify on study.design-bakery.com.

## Explicitly not included

- API keys, `.env`, OpenRouter/InferHub/Cloudflare tokens  
- Private study log content  
- Agent run logs under `/workspace/agent-runs/`  

## Sibling repos

- `Pukujan/study-os-pedagogical-IR`, `Pukujan/study-os-benchmarker`, `Pukujan/private-study-log` (private — never copy into public)  
- CGM: `Pukujan/content-generation-modules`  
- PCM: `Pukujan/project-continuity-modules`  
