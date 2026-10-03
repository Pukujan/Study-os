from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-055921\ux-defect-pass.cjs")
good = p.read_text(encoding="utf-8")
# Take good base (syntax ok, companion open works) and surgically fix A14 selectors only
old = '''        const voiceBtns = page.locator('[data-track="voice.mic"], [data-track="voice.speak"]');
        const companionVoice = panel.locator("button").filter({ hasText: /speaker|mic|mute|sound|listen/i });
        const nVoice = (await voiceBtns.count()) + (await companionVoice.count());
        if (nVoice > 0) {
          const n = Math.min(await voiceBtns.count(), 3);
          for (let i = 0; i < n; i++) {
            const btn = voiceBtns.nth(i);
            const label = (await btn.getAttribute("aria-label").catch(() => null)) || (await btn.innerText().catch(() => "")) || "";
            const before = await btn.getAttribute("aria-pressed").catch(() => null);
            const clsBefore = await btn.getAttribute("class").catch(() => "");
            recordControl("voice-control", { label });
            await btn.click().catch(() => {});
            await page.waitForTimeout(400);
            const after = await btn.getAttribute("aria-pressed").catch(() => null);
            const clsAfter = await btn.getAttribute("class").catch(() => "");
            if (!label.trim()) {
              addDefect("P2", "A14-voice-unlabeled", "Voice control has no accessible label", "Inspect mic/speaker");
              await shot(page, "fail-A14-unlabeled");
            } else if (before === after && clsBefore === clsAfter) {
              note("A14-voice-maybe-dead", `Clicked "${label}" but no visible state change`);
            } else note("A14-voice-ok", `Control "${label}" toggled`);
          }
        } else note("A14-voice", "No mic/speaker controls present on this surface");'''

# Check what's actually in 055921
idx = good.find("A14")
print("A14 idx", idx)
print(good[idx:idx+800] if idx>=0 else "none")
print("---voice section---")
idx2 = good.find("// A14")
print(good[idx2:idx2+900] if idx2>=0 else "no A14 comment")
