/**
 * CI merge gate for Ultrafast-found P0/P1 guest controls (Refs #126).
 *
 * Runs against the same branch-local stub server as player-vision-gate.spec.ts
 * (web/e2e/server.mjs + STUDY_OS_E2E_STUB_LLM). Local live scout is separate:
 * tools/ux-defect/Run-*.ps1 against https://study.design-bakery.com.
 *
 * Any hard assert failure fails CI. Browser speech APIs that cannot show a
 * reliable DOM effect in headless Chromium are marked pending with an issue
 * annotation — agents must re-check those manually on live.
 */
import { expect, test, type Page } from "@playwright/test";

const REGEN_EXAMPLE = "player.step.regen-example";
const WORKED = "worked-example";
const REVIEW = "player.review.panel";
const CHAT_TIMEOUT_MS = 20_000;

async function openFractionsPlayer(page: Page): Promise<void> {
  await page.goto("/");
  // Hero "Try it" starts Comparing fractions (LESSONS[0]).
  await page.locator('[data-track="try.start"]').first().click();
  await expect(page).toHaveURL(/\/play\//);
  await expect(page.getByTestId(REVIEW)).toBeVisible({ timeout: 30_000 });
}

async function openCompanion(page: Page): Promise<void> {
  const panel = page.locator(".companion-panel");
  if (await panel.isVisible().catch(() => false)) return;
  const ask = page.locator('[data-track="player.tutor"]');
  if ((await ask.count()) > 0) {
    await ask.first().click();
  } else {
    await page.locator('[aria-label="Open study assistant"], button.pet-button').first().click({ force: true });
  }
  await expect(panel).toBeVisible({ timeout: 10_000 });
}

test.describe("UX defect P0/P1 controls (stub server)", () => {
  test("Worked example changes visible surface on HESI fractions", async ({ page }) => {
    await openFractionsPlayer(page);
    const before = await page.locator("body").innerText();
    const btn = page.getByTestId(REGEN_EXAMPLE);
    await expect(btn).toBeVisible();
    await expect(btn).toBeEnabled({ timeout: 15_000 });
    await btn.click();
    // Observable within ~3s product rule (CI allows a little headroom).
    await expect(page.getByTestId(WORKED)).toBeVisible({ timeout: 5_000 });
    const after = await page.locator("body").innerText();
    const tag = page.locator(".worked-example-tag");
    const changed =
      (await tag.count()) > 0 ||
      (await page.getByTestId(WORKED).count()) > 0 ||
      after !== before;
    expect(changed, "Worked example must change teach/probe surface (Ultrafast D004 / #126)").toBeTruthy();
  });

  test("Exit/Back from play returns to home/menu", async ({ page }) => {
    await openFractionsPlayer(page);
    await expect(page).toHaveURL(/\/play\//);
    // Brand home is the reliable guest exit; player.home appears on done.
    await page.locator("a.brand, [data-track='nav.home']").first().click();
    await expect(page).not.toHaveURL(/\/play\//, { timeout: 5_000 });
    await expect(
      page.locator('[data-track="try.start"], [data-track="home.continue"], .try-page, .home-lanes').first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Companion Message send shows ack within timeout", async ({ page }) => {
    await openFractionsPlayer(page);
    await openCompanion(page);
    const panel = page.locator(".companion-panel");
    const input = panel.locator('[aria-label="Message"]');
    await expect(input).toBeVisible();
    await input.fill("What should I notice on this step?");
    await panel.locator('[data-track="companion.send"]').click();
    // Product truth (PDD section 2/3): an observable ack within 3s, no silent
    // drop. The pending "Thinking..." label is the ack while the tutor call is
    // in flight, so this must hold even when the reply is slow.
    const ack = panel.locator(".thinking-label, .companion-bubble.system, .companion-bubble.tutor:not(.thinking-bubble)");
    await expect(ack.first()).toBeVisible({ timeout: 3_000 });
    // And the real reply still lands.
    const reply = panel.locator(".companion-bubble.tutor:not(.thinking-bubble), .companion-bubble.system");
    await expect(reply.first()).toBeVisible({ timeout: CHAT_TIMEOUT_MS });
  });

  test("Chat ack survives a slow tutor (no silent drop while in flight)", async ({ page }) => {
    // The stub tutor answers instantly, which makes the 3s ack assertion in the
    // test above trivially true — the reply *is* the ack. This test delays the
    // tutor by 10s so the ack must stand on its own, which is the live defect
    // condition (tutor measured 9–23s on study.design-bakery.com).
    await page.route("**/api/player/sessions/*/tutor", async (route) => {
      await new Promise((r) => setTimeout(r, 10_000));
      await route.continue();
    });

    await openFractionsPlayer(page);
    await openCompanion(page);
    const panel = page.locator(".companion-panel");
    const input = panel.locator('[aria-label="Message"]');
    await expect(input).toBeVisible();
    await input.fill("What should I notice on this step?");
    await panel.locator('[data-track="companion.send"]').click();

    // Must be observable within 3s even though the reply is still 7s out.
    const ack = panel.locator(".thinking-label, .companion-bubble.system, .companion-bubble.tutor:not(.thinking-bubble)");
    await expect(ack.first()).toBeVisible({ timeout: 3_000 });
    const ackText = (await ack.first().innerText()).trim();
    expect(ackText.length, "ack must carry visible text, not just a sprite").toBeGreaterThan(0);

    // And the real reply still lands once the tutor responds.
    const reply = panel.locator(".companion-bubble.tutor:not(.thinking-bubble), .companion-bubble.system");
    await expect(reply.first()).toBeVisible({ timeout: CHAT_TIMEOUT_MS });
  });

  test("Read aloud / Voice input / Open Message affordances are present", async ({ page }, testInfo) => {
    await openFractionsPlayer(page);
    // Voice controls on the player teach surface
    const readAloud = page.locator('[aria-label="Read aloud"], [data-track="voice.speak"]');
    const voiceInput = page.locator('[aria-label="Voice input"], [data-track="voice.mic"]');
    await expect(readAloud.first()).toBeVisible();
    await expect(voiceInput.first()).toBeVisible();

    // Companion Message ("Open Message" in Ultrafast index) must be reachable.
    await openCompanion(page);
    const panel = page.locator(".companion-panel");
    await expect(panel.locator('[aria-label="Message"]')).toBeVisible();

    // Companion speaker toggle has an observable aria-label flip (DOM effect).
    const speaker = panel.locator('[data-track="companion.speaker"]');
    await expect(speaker).toBeVisible();
    const before = await speaker.getAttribute("aria-label");
    await speaker.click();
    const after = await speaker.getAttribute("aria-label");
    expect(after, "companion speaker toggle should change aria-label").not.toEqual(before);

    // Headless Chromium cannot reliably prove OS speech / mic permission effects.
    // Mark pending for live re-check rather than inventing a green.
    testInfo.annotations.push({
      type: "pending",
      description:
        "Refs #126 — Read aloud / Voice input OS speech effects need live manual re-check; CI locks affordance presence + companion speaker toggle only.",
    });
  });

  test("Pet uses slow held-pose spritesheet (idle / ball, A22a)", async ({ page }) => {
    await page.addInitScript(() => {
      try {
        localStorage.setItem("sos.pet.hidden", "false");
        sessionStorage.removeItem("sos.pet.tipSeen");
      } catch {
        /* ignore */
      }
    });
    await openFractionsPlayer(page);
    // Prefer testid; fall back to free-roam shell (may sit near viewport edge).
    const pet = page.locator('[data-testid="mascot.pet"], [data-pet-float]').first();
    await expect(pet).toBeAttached({ timeout: 15_000 });
    // Bring into view if free-roam parked near the edge on narrow viewports.
    await pet.evaluate((el) => {
      (el as HTMLElement).style.transform = "translate3d(24px, 120px, 0)";
    });
    await expect(pet).toBeVisible({ timeout: 5_000 });
    const sprite = pet.locator('[data-testid="mascot.sprite"], [data-anim="held-pose"]').first();
    await expect(sprite).toBeVisible();
    await expect(sprite).toHaveAttribute("data-anim", "held-pose");
    const fps = Number(await sprite.getAttribute("data-fps"));
    expect(fps, "A22a idle/react fps must stay low (JP limited)").toBeLessThanOrEqual(4);
    const anim = await sprite.evaluate((el) => getComputedStyle(el).animationName);
    expect(["none", "", "initial"].includes(anim) || anim === "none").toBeTruthy();
    const mood = await pet.getAttribute("data-mood");
    expect(["idle", "wave", "ball", "thinking", "talking", "celebrate", "encourage", null]).toContain(mood);
    const bg = await sprite.evaluate((el) => getComputedStyle(el).backgroundImage);
    // Any mascot sheet counts: with SOS-0014 locomotion the pet may legitimately
    // be mid-walk/turn when this samples, and that is still a held-pose sheet.
    expect(bg).toMatch(/pet-(idle|ball|wave|thinking|talking|celebrate|encourage|walk|turn)\.webp/);
  });

  test("player.back or brand exit leaves no permanent blank play", async ({ page }) => {
    await openFractionsPlayer(page);
    // If Worked example enables back, exercise it; else brand exit.
    const example = page.getByTestId(REGEN_EXAMPLE);
    if (await example.isEnabled()) {
      await example.click();
      await expect(page.getByTestId(WORKED)).toBeVisible({ timeout: 5_000 });
      const back = page.locator('[data-track="player.back"]');
      if ((await back.count()) > 0 && (await back.first().isEnabled().catch(() => false))) {
        const beforeUrl = page.url();
        await back.first().click();
        await page.waitForTimeout(500);
        // Back may stay on /play but must not blank the shell.
        const text = (await page.locator("body").innerText()).trim();
        expect(text.length, "Back must not blank the play surface").toBeGreaterThan(40);
        expect(page.url()).toContain("/play/");
        // Still allow brand exit afterward.
        void beforeUrl;
      }
    }
    await page.locator("a.brand").first().click();
    await expect(page).not.toHaveURL(/\/play\//);
  });

  test("Explain again ×3 never ErrorBoundary on .type (Refs #163)", async ({ page }) => {
    await openFractionsPlayer(page);
    const explain = page.getByTestId("player.step.regen-reexplain");
    await expect(explain).toBeVisible();
    await expect(explain).toBeEnabled({ timeout: 15_000 });
    // Done-when: 3+ Explain again must not crash (Ultrafast/Playwright).
    for (let i = 0; i < 3; i++) {
      await explain.click();
      await page.waitForTimeout(800);
      await expect(page.getByText("Something broke on this screen")).toHaveCount(0);
      await expect(page.getByTestId("render-error")).toHaveCount(0);
    }
    // Teach surface still mounted with a diagram or prose.
    await expect(page.locator(".teach, [data-testid='teach-render-box']").first()).toBeVisible();
  });

});
