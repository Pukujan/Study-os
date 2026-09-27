/**
 * Design system smoke (Refs #165). Stub server — chrome tokens only.
 */
import { expect, test } from "@playwright/test";

test.describe("Design system chrome (Refs #165)", () => {
  test("defaults dark slate and switches palette/appearance", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("data-theme-appearance", "dark");
    await expect(page.locator("html")).toHaveAttribute("data-theme-palette", "slate");

    const toggle = page.getByTestId("theme-toggle");
    await expect(toggle).toBeVisible({ timeout: 15_000 });

    await page.getByTestId("theme-open-panel").click();
    const panel = page.getByTestId("theme-panel");
    await expect(panel).toBeVisible();
    await expect(panel).toContainText("Skins chrome/UI only");

    await page.getByTestId("theme-palette").selectOption("forest");
    await expect(page.locator("html")).toHaveAttribute("data-theme-palette", "forest");

    await page.getByTestId("theme-appearance-toggle").click();
    await expect(page.locator("html")).toHaveAttribute("data-theme-appearance", "light");

    // Reload keeps preference
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme-palette", "forest");
    await expect(page.locator("html")).toHaveAttribute("data-theme-appearance", "light");
  });
});
