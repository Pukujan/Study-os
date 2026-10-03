/**
 * A13 chat-ack repro v2 — logs REQUESTS (not just responses) and waits the
 * full 20s window. Distinguishes the thinking bubble from a real tutor reply.
 */
const { chromium } = require("../../web/node_modules/playwright");

const BASE = process.argv[2] || "https://study.design-bakery.com";
const WAIT_MS = Number(process.env.WAIT_MS || 25000);

function log(...a) {
  console.log(`[${Date.now() % 100000}]`, ...a);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
  });
  const page = await ctx.newPage();

  page.on("request", (r) => {
    if (r.url().includes("/api/")) log(`REQ  ${r.method()} ${r.url().replace(BASE, "")}`);
  });
  page.on("response", (res) => {
    if (res.url().includes("/api/")) log(`RES  ${res.status()} ${res.url().replace(BASE, "")}`);
  });
  page.on("pageerror", (e) => log(`PAGEERROR ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") log(`CONSOLE[error] ${m.text().slice(0, 200)}`);
  });

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

  // Real tutor bubble = has a non-empty text body, excludes the thinking bubble.
  const realTutor = panel.locator(".companion-bubble.tutor:not(.thinking-bubble)");
  let ackAt = null;
  while (Date.now() - t0 < WAIT_MS) {
    const n = await realTutor.count();
    if (n > 0) {
      const txt = (await realTutor.first().innerText().catch(() => "")).trim();
      if (txt && !/^\.*$/.test(txt)) { ackAt = Date.now() - t0; log(`ACK at ${ackAt}ms :: ${JSON.stringify(txt.slice(0, 200))}`); break; }
    }
    await page.waitForTimeout(400);
  }
  if (ackAt === null) {
    log(`NO ACK within ${WAIT_MS}ms`);
    const thinking = await panel.locator(".thinking-bubble").count();
    const anyTutor = await realTutor.count();
    const sys = await panel.locator(".companion-bubble.system").count();
    log(`final: thinkingBubble=${thinking} realTutor=${anyTutor} system=${sys} sendDisabled=${await send.first().isDisabled()}`);
    log("panelText ::", JSON.stringify((await panel.innerText()).slice(0, 400)));
  }
  await browser.close();
})();
