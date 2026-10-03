const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await page.goto("https://study.design-bakery.com/", { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(1000);
  // start Big O
  const bigO = page.locator(".lesson-item").filter({ hasText: /Big O/i }).locator('[data-track="try.start"]');
  if (await bigO.count()) await bigO.first().click();
  else await page.locator('[data-track="try.start"]').first().click();
  await page.waitForURL(/\/play\//, { timeout: 20000 });
  await page.waitForTimeout(2000);
  const info = await page.evaluate(() => {
    const tracks = Array.from(document.querySelectorAll("[data-track]")).map(e => e.getAttribute("data-track") + "|" + (e.innerText||"").trim().slice(0,40));
    const tutor = !!document.querySelector('[data-track="player.tutor"]');
    const pet = !!document.querySelector(".pet, .mascot, [class*='pet'], [class*='mascot'], .sprite");
    const probe = !!document.querySelector("section.probe");
    const teach = !!document.querySelector("section.teach");
    return { tutor, pet, probe, teach, tracks: tracks.slice(0, 60), body: (document.body.innerText||"").slice(0, 800) };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
