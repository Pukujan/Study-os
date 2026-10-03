from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-055921\ux-defect-pass.cjs")
text = p.read_text(encoding="utf-8")
text = text.replace("await loc.click({ timeout: 8000 });", "await loc.click({ timeout: 8000, force: !!opts.force });", 1)

start = text.find("// Companion: Ask the tutor")
mid = text.find('const panel = page.locator(".companion-panel");', start)
# Find the if that opens the panel body — after const panel line
if_line = text.find("\n", mid)  # end of const panel line
# The next non-empty is the if ((await panel.count()...
rest_start = if_line + 1
# Find else note("companion"
else_note = text.find('note("companion", "Companion panel did not open")', mid)
if start < 0 or mid < 0 or else_note < 0:
    raise SystemExit(f"bad markers {start} {mid} {else_note}")

# Replace from start through just before const panel, and change else note to addDefect
open_logic = '''// Companion: Ask the tutor or force-click floating pet (animating => force)
      let companionOpened = false;
      async function tryOpenCompanion(tag) {
        if ((await page.locator('[data-track="player.tutor"]').count()) > 0) {
          if (await safeClick(page, page.locator('[data-track="player.tutor"]'), tag + "-tutor")) return true;
        }
        const petBtn = page.locator('[aria-label="Open study assistant"], button.pet-button');
        if ((await petBtn.count()) > 0) {
          if (await safeClick(page, petBtn, tag + "-pet", { force: true, waitEnabledTries: 5 })) return true;
          try {
            const box = await petBtn.first().boundingBox();
            if (box) {
              recordControl(tag + "-pet-mouse");
              await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
              await page.waitForTimeout(700);
              if (await page.locator(".companion-panel").isVisible().catch(() => false)) return true;
            }
          } catch (e) {
            recordControl(tag + "-pet-mouse-fail", { error: String(e.message || e) });
          }
        }
        return false;
      }
      companionOpened = await tryOpenCompanion("open-companion");
      if (!companionOpened) {
        const cont = page.locator('[data-testid="player.teach-continue"], [data-track="player.next"]');
        if ((await cont.count()) > 0 && (await cont.first().isEnabled().catch(() => false))) {
          await safeClick(page, cont, "continue-toward-probe");
          await page.waitForTimeout(2500);
          companionOpened = await tryOpenCompanion("open-companion-after-continue");
        }
      }
      await page.waitForTimeout(800);
      '''

text = text[:start] + open_logic + text[mid:]
# Replace soft note with defect
text = text.replace(
    'note("companion", "Companion panel did not open");',
    'addDefect("P1", "companion-open", "Could not open companion via Ask the tutor or pet", "On /play click pet (Open study assistant) or Ask the tutor"); await shot(page, "fail-companion-open");',
    1,
)
p.write_text(text, encoding="utf-8")
print("braces", text.count("{") - text.count("}"))
print("force", "force: !!opts.force" in text)
print("tryOpen", "tryOpenCompanion" in text)
