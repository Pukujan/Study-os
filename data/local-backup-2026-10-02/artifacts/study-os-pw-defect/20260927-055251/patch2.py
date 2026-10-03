from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-055251\ux-defect-pass.cjs")
text = p.read_text(encoding="utf-8")

old = '''      // Companion chips
      const openCompanion =
        (await page.locator('[data-track="player.tutor"]').count()) > 0
          ? page.locator('[data-track="player.tutor"]')
          : page.locator('button:has-text("Ask the tutor"), [aria-label*="buddy" i], .pet, .mascot');
      // Pet tap may also open
      let companionOpened = false;
      if ((await page.locator('[data-track="player.tutor"]').count()) > 0) {
        companionOpened = await safeClick(page, page.locator('[data-track="player.tutor"]'), "open-companion-tutor-link");
      }
      if (!companionOpened) {
        const pet = page.locator(".pet, .mascot, [data-track='player.pet'], button:has-text('Study buddy')");
        if ((await pet.count()) > 0) companionOpened = await safeClick(page, pet, "open-companion-pet");
      }
      await page.waitForTimeout(800);'''

new = '''      // Companion: Ask the tutor (probe Q) or pet float button (always on player)
      let companionOpened = false;
      if ((await page.locator('[data-track="player.tutor"]').count()) > 0) {
        companionOpened = await safeClick(page, page.locator('[data-track="player.tutor"]'), "open-companion-tutor-link");
      }
      if (!companionOpened) {
        const petBtn = page.locator('[aria-label="Open study assistant"], button.pet-button, .pet-float button.pet-button');
        if ((await petBtn.count()) > 0) {
          companionOpened = await safeClick(page, petBtn, "open-companion-pet");
        }
      }
      // If still closed, advance via Continue once to reach a probe with Ask the tutor
      if (!companionOpened) {
        const cont = page.locator('[data-testid="player.teach-continue"], [data-track="player.next"]');
        if ((await cont.count()) > 0) {
          await safeClick(page, cont, "continue-toward-probe");
          await page.waitForTimeout(2000);
          if ((await page.locator('[data-track="player.tutor"]').count()) > 0) {
            companionOpened = await safeClick(page, page.locator('[data-track="player.tutor"]'), "open-companion-tutor-after-continue");
          }
          if (!companionOpened) {
            const petBtn2 = page.locator('[aria-label="Open study assistant"], button.pet-button');
            if ((await petBtn2.count()) > 0) companionOpened = await safeClick(page, petBtn2, "open-companion-pet-after-continue");
          }
        }
      }
      await page.waitForTimeout(800);'''

if old not in text:
    raise SystemExit('companion open block not found')
text = text.replace(old, new)

# After A20 / before console errors, add fractions number-line sample if still guest on home
needle = '''    // Capture console errors as soft notes
    if (consoleErrors.length) {
      note("console-errors", consoleErrors.slice(0, 10).join(" | "));
    }'''

extra = '''    // Secondary sample: HESI fractions for number-line / arrows (A12)
    try {
      if (!/\\/play\\//.test(page.url())) {
        await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
        await page.waitForTimeout(1000);
      }
      // From guest home lanes or try catalog
      let fracStarted = false;
      const fracLane = page.locator(".lesson-item").filter({ hasText: /Comparing fractions|fractions/i }).locator('[data-track="home.lesson.start"], [data-track="try.start"]');
      if ((await fracLane.count()) > 0) fracStarted = await safeClick(page, fracLane, "start-fractions");
      if (!fracStarted) {
        const cont = page.locator('[data-track="home.continue"]').filter({ hasText: /fraction/i });
        if ((await cont.count()) > 0) fracStarted = await safeClick(page, cont, "continue-fractions");
      }
      if (fracStarted) {
        await page.waitForURL(/\\/play\\//, { timeout: 20000 }).catch(() => {});
        await page.waitForTimeout(2500);
        await shot(page, "10-fractions-step");
        // walk a few Continues looking for number-line
        for (let step = 0; step < 4; step++) {
          const visualOk2 = await page.evaluate(() => {
            const lines = Array.from(document.querySelectorAll("svg.number-line, .number-line, svg.visual"));
            const issues = [];
            for (const svg of lines) {
              const texts = Array.from(svg.querySelectorAll("text"));
              const boxes = texts.map((t) => { try { const b = t.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height, label: (t.textContent || "").trim() }; } catch { return null; } }).filter(Boolean);
              for (let i = 0; i < boxes.length; i++) {
                for (let j = i + 1; j < boxes.length; j++) {
                  const a = boxes[i], b = boxes[j];
                  const overlapX = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
                  const overlapY = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
                  if (overlapX > a.w * 0.5 && overlapY > a.h * 0.4) issues.push("overlap:" + a.label + "|" + b.label);
                }
              }
            }
            // BoxIndex arrows
            const arrowLabels = Array.from(document.querySelectorAll(".box-index text, .box-index .label, [class*='box-index'] text"));
            return { lineCount: lines.length, issues, arrowLabelCount: arrowLabels.length, hasFractionBar: !!document.querySelector(".fraction-bar, svg.fraction") };
          });
          if (visualOk2.lineCount > 0) {
            addCheck("A12-numberline-readable", visualOk2.issues.length === 0,
              visualOk2.issues.length ? "Overlapping labels: " + visualOk2.issues.join(",") : "number-lines=" + visualOk2.lineCount + " ok", "P2");
            if (visualOk2.issues.length) await shot(page, "fail-A12-overlap");
            else await shot(page, "11-fractions-numberline");
            break;
          }
          note("A12-fractions-step-" + step, "lines=" + visualOk2.lineCount + " arrows=" + visualOk2.arrowLabelCount + " fracBar=" + visualOk2.hasFractionBar);
          const cont2 = page.locator('[data-testid="player.teach-continue"], [data-track="player.next"]');
          if ((await cont2.count()) === 0) break;
          const okc = await safeClick(page, cont2, "fractions-continue-" + step);
          if (!okc) break;
          await page.waitForTimeout(2000);
        }
      } else {
        note("A12-fractions", "Could not start fractions lesson for number-line sample");
      }
    } catch (e) {
      note("A12-fractions-error", String(e && e.message ? e.message : e));
    }

    // Capture console errors as soft notes
    if (consoleErrors.length) {
      note("console-errors", consoleErrors.slice(0, 10).join(" | "));
    }'''

if needle not in text:
    raise SystemExit('console errors needle not found')
text = text.replace(needle, extra)

p.write_text(text, encoding='utf-8')
print('ok braces', text.count('{')-text.count('}'), 'size', len(text))
