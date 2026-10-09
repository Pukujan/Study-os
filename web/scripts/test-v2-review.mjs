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
    await page.getByTestId("v2-start").click();
    const board = page.getByTestId("v2-growth-game");
    assert.equal(await board.getAttribute("data-mission"), "cover-three");
    assert.equal(await page.getByTestId("v2-curve").getAttribute("data-live-work"), "0");

    await page.getByTestId("v2-stick").click();
    await page.getByTestId("v2-target-box:0").click();
    assert.equal(await board.getAttribute("data-placed"), "1");
    assert.equal(await page.getByTestId("v2-curve").getAttribute("data-live-work"), "1");
    assert.equal(await page.getByTestId("v2-rule-reveal").count(), 0);

    await page.getByTestId("v2-stick").click();
    await page.getByTestId("v2-target-box:0").click();
    assert.equal(await board.getAttribute("data-placed"), "1");
    await page.getByTestId("v2-stick").click();
    await page.getByTestId("v2-target-box:1").click();
    await page.getByTestId("v2-stick").click();
    await page.getByTestId("v2-target-box:2").click();
    assert.equal(await board.getAttribute("data-complete"), "true");
    assert.equal((await page.getByTestId("v2-equation").textContent())?.trim(), "3 boxes → 3 sticks");
    await page.screenshot({ path: resolve(screenshots, `v2-${label}-game.png`), fullPage: true, animations: "disabled" });
    await page.getByTestId("v2-next").click();
    assert.equal(await page.getByTestId("v2-growth-game").getAttribute("data-mission"), "cover-four");
    await page.getByTestId("v2-back").click();
    assert.equal(await page.getByTestId("v2-start").isVisible(), true);
    await page.screenshot({ path: resolve(screenshots, `v2-${label}-overview.png`), fullPage: true, animations: "disabled" });
    assert.deepEqual(problems, [], `${label}: JavaScript runtime errors`);
    assert.deepEqual(externalRequests, [], `${label}: offline review must make zero network calls`);
    console.log(`PASS offline v2 reviewer ${label} ${width}×${height}`);
    await page.close();
  }
} finally { await browser.close(); }
