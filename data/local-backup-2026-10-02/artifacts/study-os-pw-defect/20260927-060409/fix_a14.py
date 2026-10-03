from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060409\ux-defect-pass.cjs")
t = p.read_text(encoding="utf-8")
for i, line in enumerate(t.splitlines(), 1):
    if "A14-voice" in line:
        print(i, repr(line))
# Fix any broken lines by rewriting the A14 block simply
import re
pat = r'// A14 mic/speaker: companion\.mic.*?note\("A14-voice", "No companion/player mic/speaker controls in open panel"\);'
new = '''// A14 mic/speaker: companion.mic / companion.speaker (+ player voice.*)
        const voiceBtns = panel.locator('[data-track="companion.mic"], [data-track="companion.speaker"], [data-track="voice.mic"], [data-track="voice.speak"]');
        const voiceCount = await voiceBtns.count();
        if (voiceCount > 0) {
          for (let i = 0; i < Math.min(voiceCount, 4); i++) {
            const btn = voiceBtns.nth(i);
            const label = (await btn.getAttribute("aria-label").catch(() => null)) || (await btn.innerText().catch(() => "")) || "";
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
              note("A14-voice-maybe-dead", "Clicked [" + label + "] (" + track + ") but no visible class toggle");
            } else {
              note("A14-voice-ok", "Control [" + label + "] (" + track + ") toggled");
            }
          }
        } else {
          note("A14-voice", "No companion/player mic/speaker controls in open panel");
        }'''
t2, n = re.subn(pat, new, t, count=1, flags=re.S)
print("replacements", n)
if n != 1:
    raise SystemExit("replace failed")
p.write_text(t2, encoding="utf-8")
# also sync source of truth copy
Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060210\ux-defect-pass.cjs").write_text(t2, encoding="utf-8")
print("braces", t2.count("{")-t2.count("}"))
