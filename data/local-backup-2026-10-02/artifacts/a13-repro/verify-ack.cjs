/**
 * A13 post-CD live verification.
 *
 * Product truth (PDD_UX_DEFECT_EXPLORATION.md section 3): "Click -> observable
 * change within 3s, else defect". The ack must be observable on its own,
 * independent of tutor latency, so this measures time-to-ack and
 * time-to-reply separately and asserts ONLY the ack against the 3s budget.
 *
 * Usage: node verify-ack.cjs [baseUrl]
 */
const { chromium } = require("../../web/node_modules/playwright");

const BASE = process.argv[2] || "https://study.design-bakery.com";
const ACK_BUDGET_MS = 3000;

function log(...a) {
  console.log(`[${Date.now() % 1000000}]`, ...a);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
  });
  const page = await ctx.newPage();

  const tutorCalls = [];
  page.on("request", (r) => {
    if (r.url().includes("/tutor")) tutorCalls.push({ at: Date.now(), url: r.url().replace(BASE, "") });
  });
  page.on("response", (res) => {
    if (res.url().includes("/api/")) log(`RES ${res.status()} ${res.url().replace(BASE, "")}`);
  });
  page.on("pageerror", (e) => log(`PAGEERROR ${e.message}`));

  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator('[data-track="try.start"]').first().click({ timeout: 30000 });
  await page.waitForURL(/\/play\//, { timeout: 30000 });
  await page.waitForTimeout(2500);

  const panel = page.locator(".companion-panel");
  if (!(await panel.isVisible().catch(() => false))) {
    const ask = page.locator('[data-track="player.tutor"]');
    if ((await ask.count()) > 0) await ask.first().click();
    else await page.locator('[aria-label="Open study assistant"], button.pet-button').first().click({ force: true });
  }
  await panel.waitFor({ state: "visible", timeout: 15000 });

  const input = panel.locator('[aria-label="Message"]');
  await input.waitFor({ state: "visible", timeout: 10000 });
  await input.fill("What should I notice on this step?");

  const send = panel.locator('[data-track="companion.send"]');
  log("=== CLICK SEND ===");
  const t0 = Date.now();
  await send.first().click();

  // Ack = the pending thinking bubble OR any tutor/system bubble that appears.
  const ackSel = panel.locator(".thinking-label, .companion-bubble.system, .companion-bubble.tutor:not(.thinking-bubble)");
  let tAck = null;
  while (Date.now() - t0 < ACK_BUDGET_MS) {
    if ((await ackSel.count()) > 0 && (await ackSel.first().isVisible().catch(() => false))) {
      tAck = Date.now() - t0;
      log(`ACK at ${tAck}ms :: ${JSON.stringify((await ackSel.first().innerText().catch(() => "")).trim().slice(0, 120))}`);
      break;
    }
    await page.waitForTimeout(100);
  }
  if (tAck === null) {
    log(`NO ACK within ${ACK_BUDGET_MS}ms -- DEFECT`);
    log("panelText ::", JSON.stringify((await panel.innerText().catch(() => "")).slice(0, 300)));
  }

  // Reply = real tutor bubble with non-trivial text (excludes the thinking bubble).
  const reply = panel.locator(".companion-bubble.tutor:not(.thinking-bubble)");
  let tReply = null;
  while (Date.now() - t0 < 60000) {
    const n = await reply.count();
    if (n > 0) {
      const txt = (await reply.first().innerText().catch(() => "")).trim();
      if (txt && !/^\.*$/.test(txt)) {
        tReply = Date.now() - t0;
        log(`REPLY at ${tReply}ms :: ${JSON.stringify(txt.slice(0, 160))}`);
        break;
      }
    }
    await page.waitForTimeout(300);
  }
  if (tReply === null) log("NO REPLY within 60000ms");

  log("=== SUMMARY ===");
  log(`tutorCalls=${tutorCalls.length} ack=${tAck}ms (budget ${ACK_BUDGET_MS}ms) reply=${tReply}ms`);
  log(`VERDICT: ack ${tAck !== null && tAck <= ACK_BUDGET_MS ? "PASS" : "FAIL"}`);
  await browser.close();
  process.exit(tAck !== null && tAck <= ACK_BUDGET_MS ? 0 : 1);
})();
