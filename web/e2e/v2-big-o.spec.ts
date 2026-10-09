import { expect, test } from "@playwright/test";

test("v2: computer sets a mission, drag or tap validates live and unlocks algebra", async ({ page }) => {
  await page.goto("/v2");
  await expect(page.getByTestId("v2-start")).toBeVisible();
  await page.getByTestId("v2-start").click();
  const board = page.getByTestId("v2-growth-game");
  await expect(board).toHaveAttribute("data-mission", "cover-three");
  await expect(page.getByTestId("sticks-complexity-select")).toHaveCount(0);
  await expect(page.getByTestId("v2-rule-reveal")).toHaveCount(0);
  await expect(page.getByTestId("v2-curve")).toHaveAttribute("data-live-work", "0");

  // Desktop drag/drop. The same activity has a tap/keyboard fallback.
  await page.getByTestId("v2-stick").dragTo(page.getByTestId("v2-target-box:0"));
  await expect(board).toHaveAttribute("data-placed", "1");
  await expect(page.getByTestId("v2-curve")).toHaveAttribute("data-live-work", "1");
  await expect(page.getByTestId("v2-mobile-graph").locator("svg")).toHaveAttribute("data-live-work", "1");
  await page.getByTestId("v2-stick").click();
  await page.getByTestId("v2-target-box:0").click();
  await expect(board).toHaveAttribute("data-placed", "1");
  await expect(page.getByTestId("v2-game-feedback")).toContainText("Already filled");

  await page.getByTestId("v2-stick").click();
  await page.getByTestId("v2-target-box:1").click();
  await page.getByTestId("v2-stick").click();
  await page.getByTestId("v2-target-box:2").click();
  await expect(board).toHaveAttribute("data-complete", "true");
  await expect(page.getByTestId("v2-curve")).toHaveAttribute("data-live-work", "3");
  await expect(page.getByTestId("v2-equation")).toHaveText("3 boxes → 3 sticks");
  await expect(page.getByTestId("v2-rule-reveal")).not.toContainText("O(n)");
  await page.getByTestId("v2-next").click();
  await expect(page.getByTestId("v2-growth-game")).toHaveAttribute("data-mission", "cover-four");

  await page.getByTestId("v2-stick").click();
  await page.getByTestId("v2-target-box:0").click();
  await expect(page.getByTestId("v2-curve")).toHaveAttribute("data-current-n", "4");
  await expect(page.getByTestId("v2-mobile-graph")).toBeAttached();
  if (test.info().project.name === "mobile") {
    await expect(page.getByTestId("v2-mobile-graph")).toBeVisible();
    await expect(page.getByTestId("v2-curve")).toBeHidden();
  }

  await page.getByTestId("v2-back").click();
  await page.getByTestId("v2-start").click();
  await expect(page.getByTestId("v2-target-box:0")).toHaveAttribute("data-filled", "true");
  await expect(page.getByTestId("v2-curve")).toHaveAttribute("data-live-work", "1");

  await test.info().attach("v2-react-game-and-live-graph", {
    body: await page.screenshot({ fullPage: true, animations: "disabled" }),
    contentType: "image/png",
  });
});
