from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060210\ux-defect-pass.cjs")
text = p.read_text(encoding="utf-8")
old = '''        // A14 mic/speaker if present should not silently no-op without label
        const mic = panel.locator('[data-track="voice.mic"], [aria-label*="mic" i], [aria-label*="Voice" i], button:has-text("Mic")');
        const speaker = panel.locator('[data-track="voice.speak"], [aria-label*="speaker" i], [aria-label*="Read" i], button:has-text("Speaker")');
        // companion panel may have speaker/mic toggles
        const companionVoice = panel.locator("button[aria-label], button").filter({ hasText: /speaker|mic|mute|sound|listen/i });
        const voiceBtns = page.locator('[data-track="voice.mic"], [data-track="voice.speak"]');
        const voiceCount = (await voiceBtns.count()) + (await companionVoice.count());
        if (voiceCount > 0) {
          const candidates = [];
          for (let i = 0; i < (await voiceBtns.count()); i++) candidates.push(voiceBtns.nth(i));
          for (let i = 0; i < Math.min(await companionVoice.count(), 4); i++) candidates.push(companionVoice.nth(i));
          for (const btn of candidates.slice(0, 4)) {
            const label =
              (await btn.getAttribute("aria-label").catch(() => null)) ||
              (await btn.innerText().catch(() => "")) ||
              (await btn.getAttribute("title").catch(() => null)) ||
              "";
            const before = await btn.getAttribute("aria-pressed").catch(() => null);
            const clsBefore = await btn.getAttribute("class").catch(() => "");
            recordControl("voice-control", { label });
            await btn.click().catch(() => {});
            await page.waitForTimeout(400);
            const after = await btn.getAttribute("aria-pressed").catch(() => null);
            const clsAfter = await btn.getAttribute("class").catch(() => "");
            const labeled = !!(label && label.trim());
            const stateChanged = before !== after || clsBefore !== clsAfter;
            if (!labeled) {
              addDefect("P2", "A14-voice-unlabeled", "Voice control has no accessible label", "Inspect mic/speaker buttons");
              await shot(page, "fail-A14-unlabeled");
            } else if (!stateChanged) {
              // log dead control — may be browser permission; severity P2 log
              note("A14-voice-maybe-dead", `Clicked "${label}" but no visible state change (may need permission)`);
            } else {
              note("A14-voice-ok", `Control "${label}" toggled state`);
            }
          }
        } else {
          note("A14-voice", "No mic/speaker controls present on this surface");
        }'''
new = '''        // A14 mic/speaker: companion.mic / companion.speaker (+ player voice.*)
        const voiceBtns = panel.locator('[data-track="companion.mic"], [data-track="companion.speaker"], [data-track="voice.mic"], [data-track="voice.speak"]');
        const voiceCount = await voiceBtns.count();
        if (voiceCount > 0) {
          for (let i = 0; i < Math.min(voiceCount, 4); i++) {
            const btn = voiceBtns.nth(i);
            const label =
              (await btn.getAttribute("aria-label").catch(() => null)) ||
              (await btn.innerText().catch(() => "")) ||
              "";
            const track = (await btn.getAttribute("data-track").catch(() => null)) || "";
            const clsBefore = await btn.getAttribute("class").catch(() => "");
            recordControl("voice-control", { label, track });
            await btn.click({ force: true }).catch(() => {});
            await page.waitForTimeout(400);
            const clsAfter = await btn.getAttribute("class").catch(() => "");
            const labeled = !!(label && String(label).trim());
            const stateChanged = clsBefore !== clsAfter;
            if (!labeled) {
              addDefect("P2", "A14-voice-unlabeled", "Voice control has no accessible label (" + track + ")", "Inspect companion mic/speaker");
              await shot(page, "fail-A14-unlabeled");
            } else if (!stateChanged) {
              note("A14-voice-maybe-dead", "Clicked \"" + label + "\" (" + track + ") but no visible class toggle");
            } else {
              note("A14-voice-ok", "Control \"" + label + "\" (" + track + ") toggled");
            }
          }
        } else {
          note("A14-voice", "No companion/player mic/speaker controls in open panel");
        }'''
if old not in text:
    raise SystemExit("A14 block not found")
text = text.replace(old, new, 1)
p.write_text(text, encoding="utf-8")
print("ok", text.count("{")-text.count("}"))
