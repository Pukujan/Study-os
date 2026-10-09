import { expect, test } from "@playwright/test";

// Only the isolated CI preview build enables this. Production deploy keeps
// VITE_STUDY_OS_V2 unset; the classic app is unaffected. Refs #204.
test.skip(process.env.VITE_STUDY_OS_V2 !== "1", "V2 preview is disabled on this build");

test("guest reaches a coherent Big O game, equation, graph and prediction", async ({ page }) => {
  await page.goto("/v2");
  await expect(page.getByTestId("v2-start")).toBeVisible();
  await expect(page.getByText("No account needed.", { exact: false })).toBeVisible();

  await page.getByTestId("v2-start").click();
  const game = page.getByTestId("sticks-boxes-complexity");
  await expect(game).toBeVisible();
  await expect(game).toHaveAttribute("data-complexity", "O(n)");
  await expect(game).toHaveAttribute("data-n", "3");
  await expect(page.getByTestId("v2-equation")).toHaveText("W(3) = 3");
  await expect(page.getByTestId("v2-curve")).toBeVisible();

  await game.getByTestId("sticks-primary-btn").click();
  await expect(game).toHaveAttribute("data-placed", "1");
  await expect(page.getByTestId("v2-progress")).toContainText("1 of 3");

  await page.getByTestId("sticks-complexity-select").selectOption("O(n²)");
  await expect(game).toHaveAttribute("data-complexity", "O(n²)");
  await expect(game).toHaveAttribute("data-placed", "0");
  await expect(page.getByTestId("v2-equation")).toHaveText("W(3) = 3 × 3 = 9");

  await page.getByTestId("sticks-n-slider").focus();
  await page.keyboard.press("ArrowRight");
  await expect(game).toHaveAttribute("data-n", "4");
  await expect(page.getByTestId("v2-equation")).toHaveText("W(4) = 4 × 4 = 16");
  await expect(page.getByTestId("v2-curve").locator("desc")).toContainText("16 placements");

  await page.getByLabel("Number of stick placements").fill("25");
  await page.getByTestId("v2-check").click();
  await expect(page.getByTestId("v2-result")).toContainText("Yes.");

  // Returning to the overview must not create a game/algebra mismatch.
  await page.getByTestId("v2-back").click();
  await expect(page.getByTestId("v2-welcome")).toBeVisible();
  await page.getByTestId("v2-start").click();
  await expect(page.getByTestId("v2-equation")).toHaveText("W(4) = 4 × 4 = 16");
  await expect(page.getByTestId("sticks-boxes-complexity")).toHaveAttribute("data-n", "4");
  await expect(page.getByTestId("sticks-boxes-complexity")).toHaveAttribute("data-complexity", "O(n²)");

  await test.info().attach("v2-big-o-learning-surface", {
    body: await page.screenshot({ fullPage: true, animations: "disabled" }),
    contentType: "image/png",
  });
});
