# Study OS Playwright UX defect pass

- Base URL: https://study.design-bakery.com
- Finished: 2026-09-27T06:02:53.713Z
- Guest: yes
- Checks: 22 (pass 22 / fail 0)
- Defects: **0** (P0=0, P1=0, P2=0)
- Controls tried: 11

## Defects P0
_None_
## Defects P1
_None_
## Defects P2
_None_
## Controls tried
- `2026-09-27T06:02:12.933Z` **home.start-or-resume**  
- `2026-09-27T06:02:12.953Z` **try.start-big-o** click 
- `2026-09-27T06:02:16.225Z` **Explain again** click 
- `2026-09-27T06:02:18.858Z` **Worked example** click 
- `2026-09-27T06:02:35.440Z` **open-companion-pet** click 
- `2026-09-27T06:02:36.419Z` **companion-chip-first**  
- `2026-09-27T06:02:38.981Z` **companion-chat-send**  
- `2026-09-27T06:02:45.984Z` **review-score-3**  
- `2026-09-27T06:02:46.344Z` **review-submit**  
- `2026-09-27T06:02:47.999Z` **nav-home-brand** click 
- `2026-09-27T06:02:50.876Z` **start-fractions** click 

## All checks
- PASS [P0] A-home-start-resume: Guest Start/Resume/Try controls visible: 4
- PASS [P1] A23-no-classic-dsa-pir-primary: classic track attrs=0 primary=0 textPrimary=false
- PASS [P1] catalog-hesi-fractions: listed on guest home/try
- PASS [P1] catalog-dsa-big-o: listed on guest home/try
- PASS [P2] catalog-sliding-window: listed on guest home/try
- PASS [P0] A18-no-blank-white-play: play chrome ok; textLen=516
- PASS [info] player-phase-snapshot: teach=true probe=true continue=true url=https://study.design-bakery.com/play/0b681352-d7cd-4dfb-af88-ca285a2c4f64
- PASS [P0] player-teach-or-probe: teach=true probe=true continue=true
- PASS [P1] A12c-teach-no-spoil-probe: No obvious spoil; choices=0
- PASS [info] A12-numberline: No number-line SVG on this step (arrowish=0)
- PASS [P0] regen-explain-again-changes-teach: Teach content changed (textLen 261->261)
- PASS [P0] regen-worked-example-changes: Worked example surfaced (tag=true)
- PASS [info] companion-chips-count: 5
- PASS [P1] companion-chips-work: Chip click changed surface
- PASS [P1] A13-chat-ack: Tutor/system ack within 20000ms
- PASS [info] A14-voice: No mic/speaker controls present on this surface
- PASS [P1] review-no-persist-before-submit: No submitted receipt before Submit
- PASS [P1] review-persist-after-submit: Submitted receipt visible after Submit
- PASS [P0] A20-back-exit-home: Returned to menu/home at https://study.design-bakery.com/
- PASS [info] player-back-control: player.back not shown on sampled step (can_go_back may be false)
- PASS [P2] A12-numberline-readable: number-lines=2 ok
- PASS [info] console-errors: Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked. | Failed to load resource: the server responded with a status of 401 () | Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked.