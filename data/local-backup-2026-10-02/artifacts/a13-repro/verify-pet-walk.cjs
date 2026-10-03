/**
 * SOS-0014 visual verification of the mascot walk.
 *
 * The risky part of the Sprite change is frame extraction: multi-row sheets need
 * background-position computed per frame. This drives the real built app, waits
 * for the FSM to enter `walk`, and captures each distinct frame so a human can
 * confirm the legs actually cycle rather than the pet sliding.
 *
 * Usage: node verify-pet-walk.cjs [baseUrl]
 */
const { chromium } = require("../../web/node_modules/playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.argv[2] || "http://127.0.0.1:4173";
const OUT = path.join(__dirname, "pet-walk");

function log(...a) {
  console.log(`[${Date.now() % 1000000}]`, ...a);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator('[data-track="try.start"]').first().click({ timeout: 30000 });
  await page.waitForURL(/\/play\//, { timeout: 30000 });
  await page.waitForTimeout(2000);

  const float = page.locator("[data-pet-float]");
  await float.waitFor({ state: "visible", timeout: 20000 });

  // The first wander fires 6-11s after mount; give it room, then sample fast.
  const deadline = Date.now() + 60000;
  let sawWalk = false;
  const framesSeen = new Map();

  while (Date.now() < deadline) {
    const activity = await float.getAttribute("data-pet-activity");
    const facing = await float.getAttribute("data-pet-facing");
    if (activity === "walk") {
      sawWalk = true;
      const btn = float.locator(".pet-sprite");
      const box = await btn.boundingBox();
      if (box) {
        // Read the rendered frame index off the sprite's background-position.
        const pos = await btn.evaluate((el) => getComputedStyle(el).backgroundPosition);
        if (!framesSeen.has(pos)) {
          framesSeen.set(pos, true);
          const i = framesSeen.size;
          await btn.screenshot({ path: path.join(OUT, `walk-${String(i).padStart(2, "0")}.png`) });
          log(`captured frame #${i} facing=${facing} bgPos=${pos}`);
        }
      }
      if (framesSeen.size >= 6) break;
    }
    await page.waitForTimeout(60);
  }

  log(`sawWalk=${sawWalk} distinctFrames=${framesSeen.size}`);
  const last = await float.getAttribute("data-pet-activity");
  log(`finalActivity=${last}`);
  await browser.close();
  process.exit(sawWalk && framesSeen.size >= 4 ? 0 : 1);
})();
