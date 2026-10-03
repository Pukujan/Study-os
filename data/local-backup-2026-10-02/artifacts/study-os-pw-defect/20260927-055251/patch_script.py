from pathlib import Path
p = Path(r"D:\claude\Study-os\artifacts\study-os-pw-defect\20260927-055251\ux-defect-pass.cjs")
text = p.read_text(encoding="utf-8")

old_safe = """async function safeClick(page, locator, name) {
  recordControl(name, { action: \"click\" });
  try {
    await locator.first().click({ timeout: 8000 });
    return true;
  } catch (e) {
    recordControl(name, { action: \"click-fail\", error: e.message });
    return false;
  }
}"""

new_safe = """async function safeClick(page, locator, name, opts = {}) {
  recordControl(name, { action: \"click\" });
  try {
    const loc = locator.first();
    await loc.waitFor({ state: \"visible\", timeout: opts.timeout || 8000 });
    const tries = opts.waitEnabledTries || 40;
    for (let i = 0; i < tries; i++) {
      if (await loc.isEnabled().catch(() => false)) break;
      await page.waitForTimeout(250);
    }
    if (!(await loc.isEnabled().catch(() => false))) {
      recordControl(name, { action: \"click-disabled\" });
      return false;
    }
    await loc.click({ timeout: 8000 });
    return true;
  } catch (e) {
    recordControl(name, { action: \"click-fail\", error: e.message });
    return false;
  }
}"""

if old_safe not in text:
    raise SystemExit("safeClick block not found")
text = text.replace(old_safe, new_safe)

old_ex = """      if ((await exampleBtn.count()) > 0) {
        recordControl(\"Worked example\");
        await exampleBtn.first().click();
        await page.waitForTimeout(3000);
        const afterEx = await teachFingerprint(page);
        const bodyAfterEx = await bodyText(page);
        const workedTag = (await page.locator(\".worked-example-tag, [data-testid='worked-example'], .worked-example\").count()) > 0;
        const changed =
          workedTag ||
          afterEx.text !== beforeEx.text ||
          afterEx.html !== beforeEx.html ||
          bodyAfterEx !== bodyBeforeEx;
        addCheck(
          \"regen-worked-example-changes\",
          changed,
          changed
            ? `Worked example surfaced (tag=${workedTag})`
            : \"Worked example appears to be a no-op\",
          \"P0\"
        );
        if (!changed) await shot(page, \"fail-worked-example-noop\");
        else await shot(page, \"04-after-worked-example\");
      } else {
        note(\"regen-worked-example\", \"Worked example control not present\");
      }"""

new_ex = """      if ((await exampleBtn.count()) > 0) {
        const clickedEx = await safeClick(page, exampleBtn, \"Worked example\", { waitEnabledTries: 60 });
        if (!clickedEx) {
          addDefect(\"P1\", \"regen-worked-example-stuck-disabled\", \"Worked example stayed disabled / not clickable\", \"After Explain again, click Worked example\");
          await shot(page, \"fail-worked-example-disabled\");
        } else {
          await page.waitForTimeout(3500);
          const afterEx = await teachFingerprint(page);
          const bodyAfterEx = await bodyText(page);
          const workedTag = (await page.locator(\".worked-example-tag, [data-testid='worked-example'], .worked-example\").count()) > 0;
          const changed =
            workedTag ||
            afterEx.text !== beforeEx.text ||
            afterEx.html !== beforeEx.html ||
            bodyAfterEx !== bodyBeforeEx;
          addCheck(
            \"regen-worked-example-changes\",
            changed,
            changed
              ? `Worked example surfaced (tag=${workedTag})`
              : \"Worked example appears to be a no-op\",
            \"P0\"
          );
          if (!changed) await shot(page, \"fail-worked-example-noop\");
          else await shot(page, \"04-after-worked-example\");
        }
      } else {
        note(\"regen-worked-example\", \"Worked example control not present\");
      }"""

if old_ex not in text:
    raise SystemExit("example block not found")
text = text.replace(old_ex, new_ex)

old_re = """      if ((await reexplain.count()) > 0 && beforeExplain.present) {
        recordControl(\"Explain again\");
        await reexplain.first().click();
        await page.waitForTimeout(2500);"""

new_re = """      if ((await reexplain.count()) > 0 && beforeExplain.present) {
        const clickedRe = await safeClick(page, reexplain, \"Explain again\", { waitEnabledTries: 40 });
        if (!clickedRe) {
          addDefect(\"P1\", \"regen-explain-again-disabled\", \"Explain again not clickable\", \"On teach step click Explain again\");
          await shot(page, \"fail-explain-again-disabled\");
        } else {
        await page.waitForTimeout(2500);"""

if old_re not in text:
    raise SystemExit("reexplain block not found")
text = text.replace(old_re, new_re)

marker = """        if (!(changed || tagged)) await shot(page, \"fail-explain-again-noop\");
        else await shot(page, \"03-after-explain-again\");
      } else {
        note(\"regen-explain-again\", \"Explain again control or teach section not present\");
      }"""
replacement = """        if (!(changed || tagged)) await shot(page, \"fail-explain-again-noop\");
        else await shot(page, \"03-after-explain-again\");
        }
      } else {
        note(\"regen-explain-again\", \"Explain again control or teach section not present\");
      }"""
if marker not in text:
    raise SystemExit("explain close marker not found")
text = text.replace(marker, replacement)

p.write_text(text, encoding="utf-8")
print("patched ok; braces", text.count("{") - text.count("}"))
print("size", len(text))
