# Study OS Playwright UX defect pass

- Base URL: https://study.design-bakery.com
- Finished: 2026-09-27T05:59:59.956Z
- Guest: yes
- Checks: 19 (pass 19 / fail 0)
- Defects: **0** (P0=0, P1=0, P2=0)
- Controls tried: 10

## Defects P0
_None_
## Defects P1
_None_
## Defects P2
_None_
## Controls tried
- `2026-09-27T05:59:24.879Z` **home.start-or-resume**  
- `2026-09-27T05:59:24.896Z` **try.start-big-o** click 
- `2026-09-27T05:59:28.132Z` **Explain again** click 
- `2026-09-27T05:59:30.785Z` **Worked example** click 
- `2026-09-27T05:59:43.162Z` **open-companion-pet** click 
- `2026-09-27T05:59:51.179Z` **open-companion-pet** click-fail ERR locator.click: Timeout 8000ms exceeded.
Call log:
  - waiting for locator('[aria-label="Open study assistant"], button.pet-button, .pet-float button.pet-button').first()
    - locator resolved to <button type="button" class="pet-button" aria-label="Open study assistant">…</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not stable
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not stable
    - retrying click action
      - waiting 100ms
    15 × waiting for element to be visible, enabled and stable
       - element is not stable
     - retrying click action
       - waiting 500ms

- `2026-09-27T05:59:52.119Z` **review-score-3**  
- `2026-09-27T05:59:52.489Z` **review-submit**  
- `2026-09-27T05:59:54.162Z` **nav-home-brand** click 
- `2026-09-27T05:59:57.071Z` **start-fractions** click 

## All checks
- PASS [P0] A-home-start-resume: Guest Start/Resume/Try controls visible: 4
- PASS [P1] A23-no-classic-dsa-pir-primary: classic track attrs=0 primary=0 textPrimary=false
- PASS [P1] catalog-hesi-fractions: listed on guest home/try
- PASS [P1] catalog-dsa-big-o: listed on guest home/try
- PASS [P2] catalog-sliding-window: listed on guest home/try
- PASS [P0] A18-no-blank-white-play: play chrome ok; textLen=516
- PASS [info] player-phase-snapshot: teach=true probe=true continue=true url=https://study.design-bakery.com/play/93b6ef24-4ce1-4ffe-aa16-f6019dae8e65
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
- PASS [P2] A12-numberline-readable: number-lines=2 ok
- PASS [info] console-errors: Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked. | Failed to load resource: the server responded with a status of 401 () | Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked.