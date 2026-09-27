# A22a — Slow held-pose pet spritesheets (Refs #126)

**Decision (Alex):** Ship CSS/Pixi **spritesheet** loops first (A22a). Live2D (A22b) is separate. No Spine. No looping video.

## Problem

Live pet looked like it was *jizzling / shaking in place*: CSS `@keyframes` background-position competed with free-roam `transform` tweens while the idle sheet micro-moved every frame (`pet_jitter` in human-feedback).

## Fix

1. **`Sprite.tsx`** — JS discrete **held poses** (`data-anim="held-pose"`). Advances `background-position` on a timer at low fps. **No CSS animation.**
2. **`Pet.tsx`** — idle @ **2 fps**, cute **ball** loop (`pet-ball.webp`, 9 frames @ 2.5 fps) plays occasionally while idle; one-shots (wave/celebrate/…) @ 3 fps. Free-roam uses **discrete hops** (`transition: none`), not a 4.5s slide.
3. **Asset** — `web/public/mascot/pet-ball.webp` letterboxed from `duo-starplay` into the pet 144×176 frame so size does not jump.
4. **No Live2D** in this slice.

## Verify

```bash
cd web && npm test -- src/mascot
cd web && npx playwright test e2e/ux-defect-controls.spec.ts -g 'held-pose'
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com   # after deploy / against preview
```

## Out of scope

- Full walk/turn locomotion (#121 / S4)
- A22b Live2D Cubism
- Pixi runtime (kept CSS background-image + JS holds; Pixi optional later)
