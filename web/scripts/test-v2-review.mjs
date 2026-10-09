import assert from "node:assert/strict";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "@playwright/test";

const web = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const review = pathToFileURL(resolve(web, "dist-review", "review.html")).href;
const screenshots = resolve(web, "dist-review", "screenshots");
mkdirSync(screenshots, { recursive: true });

const browser = await chromium.launch({ headless: true });
try {
  for (const { label, width, height } of [
    { label: "mobile", width: 390, height: 844 },
    { label: "desktop", width: 1440, height: 900 },
  ]) {
    const page = await browser.newPage({ viewport: { width, height } });
    const problems = [];
    const externalRequests = [];
    page.on("pageerror", (error) => problems.push(error.message));
    page.on("request", (request) => {
      if (/^https?:/i.test(request.url())) externalRequests.push(request.url());
    });
    await page.goto(review);
    await page.getByTestId("v2-start").waitFor();
    assert.match(await page.title(), /Study OS v2/);
    assert.equal(await page.getByTestId("v2-start").isVisible(), true);
    await page.getByTestId("v2-start").click();
    const game = page.getByTestId("sticks-boxes-complexity");
    assert.equal(await game.getAttribute("data-n"), "3");
    assert.equal((await page.getByTestId("v2-equation").textContent())?.trim(), "W(3) = 3");
    await game.getByTestId("sticks-primary-btn").click();
    assert.equal(await game.getAttribute("data-placed"), "1");
    await game.getByTestId("sticks-complexity-select").selectOption("O(n²)");
    assert.equal((await page.getByTestId("v2-equation").textContent())?.trim(), "W(3) = 3 × 3 = 9");
    assert.equal(await game.getAttribute("data-placed"), "0");
    await page.getByLabel("Number of stick placements").fill("16");
    await page.getByTestId("v2-check").click();
    assert.match(await page.getByTestId("v2-result").textContent(), /Not quite/);
    await page.getByLabel("Number of stick placements").fill("16");
    await page.getByTestId("v2-check").click();
    assert.match(await page.getByTestId("v2-result").textContent(), /Not quite/);
    await page.getByLabel("Number of stick placements").fill("16");
    // Deliberately wrong prediction for n=4? Under O(n²), 16 IS correct.
    assert.match(await page.getByTestId("v2-result").textContent(), /Not quite/);
    await page.getByTestId("v2-back").click();
    assert.equal(await page.getByTestId("v2-start").isVisible(), true);
    await page.screenshot({ path: resolve(screenshots, `v2-${label}.png`), fullPage: true, animations: "disabled" });
    assert.deepEqual(problems, [], `${label}: JavaScript runtime errors`);
    assert.deepEqual(externalRequests, [], `${label}: offline review must make zero network calls`);
    console.log(`PASS offline v2 reviewer ${label} ${width}×${height}`);
    await page.close();
  }
} finally {
  await browser.close();
}
