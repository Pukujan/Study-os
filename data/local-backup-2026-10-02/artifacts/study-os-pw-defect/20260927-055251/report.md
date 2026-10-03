# Study OS Playwright UX defect pass

- Base URL: https://study.design-bakery.com
- Finished: 2026-09-27T05:58:00.447Z
- Guest: yes
- Checks: 18 (pass 18 / fail 0)
- Defects: **0** (P0=0, P1=0, P2=0)
- Controls tried: 7

## Defects P0
_None_
## Defects P1
_None_
## Defects P2
_None_
## Controls tried
- `2026-09-27T05:57:35.606Z` **home.start-or-resume**  
- `2026-09-27T05:57:35.632Z` **try.start-big-o** click 
- `2026-09-27T05:57:38.968Z` **Explain again** click 
- `2026-09-27T05:57:41.606Z` **Worked example** click 
- `2026-09-27T05:57:56.471Z` **review-score-3**  
- `2026-09-27T05:57:56.873Z` **review-submit**  
- `2026-09-27T05:57:58.549Z` **nav-home-brand** click 

## All checks
- PASS [P0] A-home-start-resume: Guest Start/Resume/Try controls visible: 4
- PASS [P1] A23-no-classic-dsa-pir-primary: classic track attrs=0 primary=0 textPrimary=false
- PASS [P1] catalog-hesi-fractions: listed on guest home/try
- PASS [P1] catalog-dsa-big-o: listed on guest home/try
- PASS [P2] catalog-sliding-window: listed on guest home/try
- PASS [P0] A18-no-blank-white-play: play chrome ok; textLen=516
- PASS [info] player-phase-snapshot: teach=true probe=true continue=true url=https://study.design-bakery.com/play/bb6ff63c-8efc-439a-b505-23b02a1926b9
- PASS [P0] player-teach-or-probe: teach=true probe=true continue=true
- PASS [P1] A12c-teach-no-spoil-probe: No obvious spoil; choices=0
- PASS [info] A12-numberline: No number-line SVG on this step (arrowish=0)
- PASS [P0] regen-explain-again-changes-teach: Teach content changed (textLen 261->261)
- PASS [P0] regen-worked-example-changes: Worked example surfaced (tag=true)
- PASS [info] companion: Companion panel did not open
- PASS [P1] review-no-persist-before-submit: No submitted receipt before Submit
- PASS [P1] review-persist-after-submit: Submitted receipt visible after Submit
- PASS [P0] A20-back-exit-home: Returned to menu/home at https://study.design-bakery.com/
- PASS [info] player-back-control: player.back not shown on sampled step (can_go_back may be false)
- PASS [info] console-errors: Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked. | Failed to load resource: the server responded with a status of 401 ()