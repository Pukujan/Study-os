# Study OS Playwright UX defect pass

- Base URL: https://study.design-bakery.com
- Finished: 2026-09-27T06:07:47.272Z
- Guest: yes
- Checks: 23 (pass 22 / fail 1)
- Defects: **1** (P0=0, P1=1, P2=0)
- Controls tried: 13

## Defects P0
_None_
## Defects P1
### A13-chat-ack
- Detail: No chat ack within 20000ms after companion send. Intermittent vs prior pass at 20260927-060210. Soft-fail continued suite.
- Repro: Guest open https://study.design-bakery.com -> Try Big O -> open companion via pet (aria-label Open study assistant; may need force click — pet float animates) -> Send chat 'What should I notice on this step?' -> wait 20s. Expected: tutor/system bubble ack. Observed: no tutor/system bubble within 20s (screenshot fail-A13-chat-silent.png). Note: same check passed in prior run 20260927-060210; console also shows intermittent 401 resource failures.

## Defects P2
_None_
## Controls tried
- `2026-09-27T06:06:54.556Z` **home.start-or-resume**  
- `2026-09-27T06:06:54.575Z` **try.start-big-o** click 
- `2026-09-27T06:06:57.836Z` **Explain again** click 
- `2026-09-27T06:07:00.465Z` **Worked example** click 
- `2026-09-27T06:07:14.690Z` **open-companion-pet** click 
- `2026-09-27T06:07:15.678Z` **companion-chip-first**  
- `2026-09-27T06:07:18.227Z` **companion-chat-send**  
- `2026-09-27T06:07:38.431Z` **voice-control**  
- `2026-09-27T06:07:38.917Z` **voice-control**  
- `2026-09-27T06:07:39.506Z` **review-score-3**  
- `2026-09-27T06:07:39.875Z` **review-submit**  
- `2026-09-27T06:07:41.512Z` **nav-home-brand** click 
- `2026-09-27T06:07:44.382Z` **start-fractions** click 

## All checks
- PASS [P0] A-home-start-resume: Guest Start/Resume/Try controls visible: 4
- PASS [P1] A23-no-classic-dsa-pir-primary: classic track attrs=0 primary=0 textPrimary=false
- PASS [P1] catalog-hesi-fractions: listed on guest home/try
- PASS [P1] catalog-dsa-big-o: listed on guest home/try
- PASS [P2] catalog-sliding-window: listed on guest home/try
- PASS [P0] A18-no-blank-white-play: play chrome ok; textLen=516
- PASS [info] player-phase-snapshot: teach=true probe=true continue=true url=https://study.design-bakery.com/play/0be10ee4-b6cf-4e6f-8cd1-da04f5fbe133
- PASS [P0] player-teach-or-probe: teach=true probe=true continue=true
- PASS [P1] A12c-teach-no-spoil-probe: No obvious spoil; choices=0
- PASS [info] A12-numberline: No number-line SVG on this step (arrowish=0)
- PASS [P0] regen-explain-again-changes-teach: Teach content changed (textLen 261->261)
- PASS [P0] regen-worked-example-changes: Worked example surfaced (tag=true)
- PASS [info] companion-chips-count: 5
- PASS [P1] companion-chips-work: Chip click changed surface
- FAIL [P1] A13-chat-ack: No chat ack within 20000ms (silent forever?)
- PASS [info] A14-voice-ok: Control "Voice input" toggled state
- PASS [info] A14-voice-ok: Control "Turn on read aloud" toggled state
- PASS [P1] review-no-persist-before-submit: No submitted receipt before Submit
- PASS [P1] review-persist-after-submit: Submitted receipt visible after Submit
- PASS [P0] A20-back-exit-home: Returned to menu/home at https://study.design-bakery.com/
- PASS [info] player-back-control: player.back not shown on sampled step (can_go_back may be false)
- PASS [P2] A12-numberline-readable: number-lines=2 ok
- PASS [info] console-errors: Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked. | Failed to load resource: the server responded with a status of 401 () | Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked.