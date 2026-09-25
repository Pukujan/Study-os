# Study OS character bible (SOS-0005, Refs #103)

Two original, canonical characters. **All future art uses the reference images in `refs/` and the fixed prompt blocks in `prompts/`.** Do not redesign them per asset. General art (lesson illustrations, onboarding, lane cards, empty states, hero) uses the **mature anime** style (see `refs/pair-key-art.webp`, style anchor CGM `assets/marketing/story-loop-square.png`). The in-app mascot uses the **chibi** versions.

Status: canonical references accepted by the orchestrator; owner (Alex) review pending. Provenance for every file is in `../asset-manifest.json` (model, prompt sha256, reference hashes, final hash).

## Roles (binding, Alex 2026-09-24)

| Character | Mature form | Chibi form | In-app role |
|---|---|---|---|
| **Learner** (placeholder name, human) | art, onboarding, lane cards, hero | **the PET / main in-app mascot** | Tap to open the companion panel. Talks (talking loop + browser TTS + speech bubble with the live transcript), reacts to answers (celebrate / encourage), thinks while the tutor is generating, waves on greet, idles otherwise. |
| **Helper** (placeholder name, robot) | supporting figure in art | **supporting chibi robot** | Never the main mascot and never speaks for the tutor. **Idle only:** after the learner has been idle for a while it occasionally rolls/hovers in, plays with the pet (head-pat or star-play loop), and leaves. |

### Robot visit rules
- Trigger: >= 90 s with no input while the companion is idle, at most once per 10 min, at most ~6 s on screen.
- Never during an assessment probe, never while the learner is typing or speaking, never while the pet is talking / thinking / reacting, never when the panel is showing a variant or worked example transition.
- Off under `prefers-reduced-motion` (the pet shows a static first frame) and when the mascot is muted/hidden.
- Sequence: `robot-hover` strip slides in from the edge (CSS transform, ~1.2 s) -> one pass of `duo-headpat` or `duo-starplay` (pet+robot together, 9 frames) -> robot slides out -> back to `pet-idle`.
- Scale: duo frames contain the pet at ~0.77 of `pet-idle` height; render duo sprites at 1.3x the pet frame scale so the pet does not jump in size.

## Canonical references (`refs/`)
- `learner-turnaround.webp` front / three-quarter / side
- `learner-expressions.webp` expression sheet
- `helper-turnaround.webp`, `helper-expressions.webp`
- `pair-key-art.webp` mature anime key art (style anchor for general art)
- `learner-chibi-master.webp` chibi pet master; `helper-chibi-master.webp` chibi robot master

## Written spec
### Learner (human)
- Adult woman, late twenties, career-switcher studying in the evenings. Mature form ~7 heads tall, realistic adult body; never childlike. Chibi form ~2.5 heads.
- Face: soft oval, calm dark-brown almond eyes, thin straight brows, small nose, warm light-brown skin, **beauty mark under the left eye**.
- Hair: shoulder-length wavy black with violet sheen, side-swept fringe, **coral hair clip on the right**.
- Outfit: oversized violet #8F7CFF knit cardigan, cream #F4F1FF crew-neck tee, night-ink #111B4D straight trousers, white sneakers, thin gold #FFD28A star pendant. No glasses.
- Personality: curious, determined, a little tired but warm; friendly half-smile. As the pet she is a study buddy, not an authority: she never claims mastery for the learner.

### Helper (robot)
- Cat-sized hovering companion. Smooth egg-shaped cream #F4F1FF shell, no legs, cyan #63D9FF hover glow, two floating mitten hands.
- Face: glossy night-ink visor with two large rounded cyan eyes (expressions only via screen eyes, optional small mouth line).
- Head: two short rounded violet fin-ears, tiny gold star antenna. Mint #94E3CB knitted scarf, small coral #FF8A70 chest light.
- Personality: patient, playful, curious; never smug. Non-verbal in the app.

### Palette (CGM)
night ink #111B4D, violet #8F7CFF, cyan #63D9FF, coral #FF8A70, cream #F4F1FF, mint #94E3CB, gold #FFD28A. Blue-violet evening light with warm accents.

## Fixed prompt blocks (`prompts/`)
- `block-learner.txt`, `block-robot.txt`, `block-style.txt` are the fixed, reusable blocks. Every prompt = asset-specific instruction + the relevant character block(s) + style block, with the canonical refs attached as image inputs.
- Full prompts used: `*-turn.full.txt`, `*-expr.full.txt`, `pair-key.full.txt`, `*-chibi.full.txt`, loop prompts `loop-common.txt` + `pet-*.full.txt`, duo prompts `duo-common.txt` + `duo-*.full.txt`.

## Model and settings
- Model: `cb/gemini-3.1-flash-image` via InferHub chat completions, `modalities: ["image","text"]`, one candidate per call, 2 candidates (a/b) per asset, orchestrator picks after review. No seed support: reproducibility = prompt file + sha256 + reference image hashes (see manifest).
- Reference inputs: style anchor CGM `story-loop-square.png`; for everything after the turnarounds, the canonical turnaround + chibi master of the character(s) involved.
- Loops: generated as a 3x2 (pet, 6 frames) or 3x3 (duo, 9 frames) sheet on flat chroma green, then processed by `sprites.py`: chroma key + despill, grid split, edge grid-line removal, union-bbox alignment on one canvas, transparent WebP strip (pet 144x176, duo 216x144, robot-hover 120x160), GIF preview.
- Rejected: `robot-turn-b` (baked-in text labels); first SVG fox mascot (Alex: a hand-authored SVG is not a substitute for an image).

## Sprite set (`web/public/mascot/`)
| file | frames | use |
|---|---|---|
| pet-idle.webp | 6 | breathe, blink, small fidgets (default) |
| pet-wave.webp | 6 | greet on open / session start |
| pet-thinking.webp | 6 | tutor generating |
| pet-talking.webp | 6 | while TTS speaks / bubble streams |
| pet-celebrate.webp | 6 | correct answer (short, once) |
| pet-encourage.webp | 6 | wrong / confused (supportive, never mocking) |
| duo-headpat.webp | 9 | idle robot visit loop A |
| duo-starplay.webp | 9 | idle robot visit loop B |
| robot-hover.webp | 6 | robot entering / leaving |

Playback: CSS `steps(N)` on `background-position` (or a tiny React component), ~6-8 fps, paused (first frame) under `prefers-reduced-motion`; pet rendered at <= 96 px (mobile) / 120 px (desktop) tall, never covering the question card; mute/hide toggle.
