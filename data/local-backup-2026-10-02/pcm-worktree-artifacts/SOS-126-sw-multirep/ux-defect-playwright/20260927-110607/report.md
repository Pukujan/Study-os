# Study OS Playwright UX defect pass

- Base URL: https://study.design-bakery.com
- Finished: 2026-09-27T15:06:36.495Z
- Guest: yes
- Checks: 23 (pass 23 / fail 0)
- Defects: **0** (P0=0, P1=0, P2=0)
- Controls tried: 13

## Defects P0
_None_
## Defects P1
_None_
## Defects P2
_None_
## Controls tried
- `2026-09-27T15:06:13.817Z` **home.start-or-resume**  
- `2026-09-27T15:06:13.827Z` **try.start-big-o** click 
- `2026-09-27T15:06:17.490Z` **Explain again** click 
- `2026-09-27T15:06:20.134Z` **Worked example** click 
- `2026-09-27T15:06:23.813Z` **open-companion-pet** click 
- `2026-09-27T15:06:24.855Z` **companion-chip-first**  
- `2026-09-27T15:06:27.422Z` **companion-chat-send**  
- `2026-09-27T15:06:27.664Z` **voice-control**  
- `2026-09-27T15:06:28.132Z` **voice-control**  
- `2026-09-27T15:06:28.745Z` **review-score-3**  
- `2026-09-27T15:06:29.106Z` **review-submit**  
- `2026-09-27T15:06:30.774Z` **nav-home-brand** click 
- `2026-09-27T15:06:33.660Z` **start-fractions** click 

## All checks
- PASS [P0] A-home-start-resume: Guest Start/Resume/Try controls visible: 4
- PASS [P1] A23-no-classic-dsa-pir-primary: classic track attrs=0 primary=0 textPrimary=false
- PASS [P1] catalog-hesi-fractions: listed on guest home/try
- PASS [P1] catalog-dsa-big-o: listed on guest home/try
- PASS [P2] catalog-sliding-window: listed on guest home/try
- PASS [P0] A18-no-blank-white-play: play chrome ok; textLen=446
- PASS [info] player-phase-snapshot: teach=true probe=true continue=true url=https://study.design-bakery.com/play/09e25911-6365-42af-8e4e-2edd7d5664eb
- PASS [P0] player-teach-or-probe: teach=true probe=true continue=true
- PASS [P1] A12c-teach-no-spoil-probe: No obvious spoil; choices=0
- PASS [info] A12-numberline: No number-line SVG on this step (arrowish=0)
- PASS [P0] regen-explain-again-changes-teach: Teach content changed (textLen 178->178)
- PASS [P0] regen-worked-example-changes: Worked example surfaced (tag=true)
- PASS [info] companion-chips-count: 5
- PASS [P1] companion-chips-work: Chip click changed surface
- PASS [P1] A13-chat-ack: Tutor/system ack within 20000ms
- PASS [info] A14-voice-ok: Control "Voice input" toggled state
- PASS [info] A14-voice-ok: Control "Turn on read aloud" toggled state
- PASS [P1] review-no-persist-before-submit: No submitted receipt before Submit
- PASS [P1] review-persist-after-submit: Submitted receipt visible after Submit
- PASS [P0] A20-back-exit-home: Returned to menu/home at https://study.design-bakery.com/
- PASS [info] player-back-control: player.back not shown on sampled step (can_go_back may be false)
- PASS [info] A12-fractions-step-0: lines=0 arrows=0 fracBar=false
- PASS [info] console-errors: Executing inline script violates the following Content Security Policy directive 'script-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-5wpErWKRYpcEecHyzvbxJbcb9NpW5dq5CyMWDstRxtA='), or a nonce ('nonce-...') is required to enable inline execution. The action has been blocked. | Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked. | Failed to load resource: the server responded with a status of 401 () | Executing inline script violates the following Content Security Policy directive 'script-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-5wpErWKRYpcEecHyzvbxJbcb9NpW5dq5CyMWDstRxtA='), or a nonce ('nonce-...') is required to enable inline execution. The action has been blocked. | Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495' violates the following Content Security Policy directive: "script-src 'self'". Note that 'script-src-elem' was not explicitly set, so 'script-src' is used as a fallback. The action has been blocked.