# A22a — Slow held-pose pet spritesheets (Refs #126)

**Decision (Alex):** Ship CSS/Pixi **spritesheet** loops first (A22a). Live2D (A22b) is separate. No Spine. No looping video.

## Problem

Live pet looked like it was *jizzling / shaking in place*: CSS `@keyframes` background-position competed with free-roam `transform` tweens while the idle sheet micro-moved every frame (`pet_jitter` in human-feedback).

## Fix

1. **`Sprite.tsx`** — JS discrete **held poses** (`data-anim="held-pose"`). Advances `background-position` on a timer at low fps. **No CSS animation.**
2. **`Pet.tsx`** — idle @ **2 fps**, cute **ball** loop (`pet-ball.webp`, 9 frames @ 2.5 fps) plays occasionally while idle; one-shots (wave/celebrate/…) @ 3 fps. Free-roam uses **discrete hops** (`transition: none`), not a 4.5s slide.
3. **Asset** — `web/public/mascot/pet-ball.webp` letterboxed from `duo-starplay` into the pet 144×176 frame so size does not jump.
4. **No Live2D** in this slice.

## Relationship to SOS-0014 locomotion

A22a (held poses) and SOS-0014 (#121/#173, real walk/turn) are **complementary, not alternatives** — they fix the same live jitter from two directions and now ship together:

| | A22a | SOS-0014 |
| --- | --- | --- |
| `Sprite.tsx` | replaces CSS `@keyframes` with a JS timer | adds `cols`/`frame`/`mirrored` for multi-row sheets |
| `Pet.tsx` | low-fps mood loops, `transition: none` | pure locomotion FSM (`locomotion.ts`) owns the clock |

The merged `Sprite` steps discrete poses itself, and accepts an explicit `frame` when the caller owns the clock — which multi-row walk/turn sheets require, since a background-position keyframe can only walk one axis. The float shell carries `transition: none` so the FSM's `translate3d` writes never tween.

## Verify

```bash
cd web && npm test -- src/mascot
cd web && npx playwright test e2e/ux-defect-controls.spec.ts -g 'held-pose'
./tools/frontend_qa/run_ultrafast_scout.sh https://study.design-bakery.com   # after deploy / against preview
```

## Out of scope

- A22b Live2D Cubism
- Pixi runtime (kept CSS background-image + JS holds; Pixi optional later)

Walk/turn locomotion was out of scope for A22a itself and has since landed as SOS-0014 (#173) — see the relationship table above.
