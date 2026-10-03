const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await page.goto("https://study.design-bakery.com/", { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(800);
  await page.locator('[data-track="try.start"]').first().click();
  await page.waitForURL(/\/play\//, { timeout: 20000 });
  await page.waitForTimeout(1500);
  const pet = page.locator('[aria-label="Open study assistant"], button.pet-button');
  console.log("pet count", await pet.count());
  if (await pet.count()) {
    const box = await pet.first().boundingBox();
    console.log("box", box);
    console.log("visible", await pet.first().isVisible());
    console.log("enabled", await pet.first().isEnabled());
    await pet.first().click({ force: true, timeout: 5000 }).catch(e => console.log("click err", e.message));
    await page.waitForTimeout(1000);
    console.log("panel", await page.locator(".companion-panel").count(), "visible", await page.locator(".companion-panel").isVisible().catch(()=>false));
    // try dispatch tap via evaluate
    await page.evaluate(() => {
      const b = document.querySelector('[aria-label="Open study assistant"]');
      if (!b) return;
      b.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, pointerId: 1, button: 0, clientX: 10, clientY: 10 }));
      b.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, pointerId: 1, button: 0, clientX: 10, clientY: 10 }));
      b.click();
    });
    await page.waitForTimeout(1000);
    console.log("panel after eval", await page.locator(".companion-panel").count(), await page.locator(".companion-panel").isVisible().catch(()=>false));
  }
  // also try Ask tutor after continue until probe choices
  for (let i=0;i<5;i++) {
    const tutor = page.locator('[data-track="player.tutor"]');
    if (await tutor.count()) { console.log("tutor at step", i); await tutor.click(); break; }
    const c = page.locator('[data-track="player.next"], [data-testid="player.teach-continue"]');
    if (!(await c.count())) break;
    if (!(await c.first().isEnabled())) break;
    await c.first().click().catch(()=>{});
    await page.waitForTimeout(1500);
  }
  console.log("final tutor", await page.locator('[data-track="player.tutor"]').count());
  console.log("final panel", await page.locator(".companion-panel").isVisible().catch(()=>false));
  console.log("body", (await page.locator("body").innerText()).slice(0,500));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
