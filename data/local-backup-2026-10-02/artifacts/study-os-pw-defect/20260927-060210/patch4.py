from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-060210\ux-defect-pass.cjs")
text = p.read_text(encoding="utf-8")
marker = 'note("A12-fractions-step-" + step, "lines=" + visualOk2.lineCount + " arrows=" + visualOk2.arrowLabelCount + " fracBar=" + visualOk2.hasFractionBar);'
insert = r'''// A14: mic/speaker on probe answer surface
          const voiceBtns2 = page.locator('[data-track="voice.mic"], [data-track="voice.speak"]');
          if ((await voiceBtns2.count()) > 0 && step === 0) {
            for (let vi = 0; vi < Math.min(await voiceBtns2.count(), 2); vi++) {
              const btn = voiceBtns2.nth(vi);
              const label = (await btn.getAttribute("aria-label").catch(() => null)) || (await btn.innerText().catch(() => "")) || "";
              const track = (await btn.getAttribute("data-track").catch(() => null)) || "";
              recordControl("fractions-voice", { label, track });
              const before = await btn.getAttribute("class").catch(() => "");
              await btn.click({ force: true }).catch(() => {});
              await page.waitForTimeout(400);
              const after = await btn.getAttribute("class").catch(() => "");
              if (!String(label).trim() && !track) {
                addDefect("P2", "A14-voice-unlabeled", "Voice control missing label", "Inspect mic/speaker on fractions probe");
                await shot(page, "fail-A14-unlabeled");
              } else {
                note("A14-voice-present", track + " label=" + label + " classChanged=" + (before !== after));
              }
            }
          } else if (step === 0) {
            note("A14-voice-fractions", "No voice.mic/speak on this fractions step yet");
          }
          // A12c on fractions if teach+choices
          if ((await page.locator("section.teach").count()) > 0 && (await page.locator('[data-track^="player.choice"], .btn.choice').count()) > 0) {
            const spoil2 = await page.evaluate(() => {
              const teach = document.querySelector("section.teach");
              const probe = document.querySelector("section.probe");
              if (!teach || !probe) return { spoiled: false };
              const teachText = (teach.innerText || "").toLowerCase();
              const choices = Array.from(probe.querySelectorAll('[data-track^="player.choice"], .btn.choice')).map(b => (b.innerText||"").trim()).filter(Boolean);
              const hits = choices.filter(c => c.length >= 2 && teachText.includes(c.toLowerCase()));
              // spoiling = teach states the correct answer explicitly, not merely naming both fractions
              const spoilPhrase = /answer\s+is\b|correct\s+answer\b|bigger\s+is\b|therefore\s+[0-9]/i.test(teachText);
              return { spoiled: spoilPhrase, hits, choiceCount: choices.length };
            });
            addCheck("A12c-fractions-teach-no-spoil", !spoil2.spoiled,
              spoil2.spoiled ? JSON.stringify(spoil2) : "No explicit answer spoiler on fractions teach+probe", "P1");
          }
          note("A12-fractions-step-" + step, "lines=" + visualOk2.lineCount + " arrows=" + visualOk2.arrowLabelCount + " fracBar=" + visualOk2.hasFractionBar);'''
if marker not in text:
    raise SystemExit("marker missing")
text = text.replace(marker, insert, 1)
p.write_text(text, encoding="utf-8")
print("braces", text.count("{")-text.count("}"))
