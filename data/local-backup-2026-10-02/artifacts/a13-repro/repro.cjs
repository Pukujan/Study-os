/**
 * A13 chat-ack repro against live. Captures network status per /api/ call,
 * console errors, and the companion panel DOM over time.
 *
 * Usage: node repro.cjs [baseUrl]
 */
const { chromium } = require("../../web/node_modules/playwright");

const BASE = process.argv[2] || "https://study.design-bakery.com";
const STAMP = new Date().toISOString().replace(/[:.]/g, "-");

function log(...a) {
  console.log(`[${new Date().toISOString()}]`, ...a);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
  });
  const page = await ctx.newPage();

  const apiCalls = [];
  page.on("response", async (res) => {
    const u = res.url();
    if (u.includes("/api/")) {
      let body = "";
      try {
        if (!res.ok()) body = (await res.text()).slice(0, 300);
      } catch { /* ignore */ }
      apiCalls.push({ url: u.replace(BASE, ""), status: res.status(), method: res.request().method(), body });
      log(`NET ${res.status()} ${res.request().method()} ${u.replace(BASE, "")}${body ? " :: " + body : ""}`);
    }
  });
  const consoleMsgs = [];
  page.on("console", (m) => {
    consoleMsgs.push({ type: m.type(), text: m.text() });
    if (m.type() === "error" || m.type() === "warning") log(`CONSOLE[${m.type()}] ${m.text()}`);
  });
  page.on("pageerror", (e) => log(`PAGEERROR ${e.message}`));

  log("goto", BASE);
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 });

  // Hero Try -> fractions (LESSONS[0]) per CI spec
  log("click try.start");
  await page.locator('[data-track="try.start"]').first().click({ timeout: 30000 });
  await page.waitForURL(/\/play\//, { timeout: 30000 });
  log("url now", page.url());
  await page.waitForTimeout(3000);

  // Open companion
  log("open companion");
  const panel = page.locator(".companion-panel");
  if (!(await panel.isVisible().catch(() => false))) {
    const ask = page.locator('[data-track="player.tutor"]');
    if ((await ask.count()) > 0) await ask.first().click();
    else await page.locator('[aria-label="Open study assistant"], button.pet-button').first().click({ force: true });
  }
  await panel.waitFor({ state: "visible", timeout: 15000 });
  log("companion visible");

  const input = panel.locator('[aria-label="Message"]');
  await input.waitFor({ state: "visible", timeout: 10000 });
  log("input visible; filling");
  await input.fill("What should I notice on this step?");

  const send = panel.locator('[data-track="companion.send"]');
  log("send count", await send.count(), "disabled", await send.first().isDisabled());
  const t0 = Date.now();
  await send.first().click();
  log("clicked send at t=0");

  // Poll panel state
  let sawThinking = false;
  let sawTutor = false;
  const seen = new Set();
  for (let i = 0; i < 50; i++) {
    const txt = (await panel.innerText().catch(() => "")).trim();
    if (txt && !seen.has(txt)) {
      seen.add(txt);
      log(`PANEL t=${Date.now() - t0}ms :: ${JSON.stringify(txt.slice(0, 400))}`);
    }
    const thinking = await panel.locator(".thinking-bubble").count();
    const tutor = await panel.locator(".companion-bubble.tutor").count();
    const sys = await panel.locator(".companion-bubble.system").count();
    const learner = await panel.locator(".companion-bubble.learner").count();
    if (thinking > 0) sawThinking = true;
    if (tutor > 0) sawTutor = true;
    if (i % 4 === 0) log(`STATE t=${Date.now() - t0}ms thinking=${thinking} tutor=${tutor} system=${sys} learner=${learner} sendDisabled=${await send.first().isDisabled()}`);
    if (tutor > 0 && i > 2) break;
    await page.waitForTimeout(500);
  }

  log("=== SUMMARY ===");
  log("sawThinking", sawThinking, "sawTutorBubble", sawTutor);
  log("apiCalls", JSON.stringify(apiCalls, null, 2));
  log("consoleErrors", JSON.stringify(consoleMsgs.filter((m) => m.type === "error"), null, 2));
  await page.screenshot({ path: `artifacts/a13-repro/${STAMP}.png`, fullPage: false }).catch(() => {});
  await browser.close();
})();
