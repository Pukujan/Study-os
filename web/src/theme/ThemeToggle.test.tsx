import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { act } from "react";
import { ThemeProvider } from "./ThemeProvider";
import ThemeToggle from "./ThemeToggle";
import { render } from "../test-utils";

describe("ThemeToggle", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => localStorage.clear());

  it("opens panel with palette/type/mood/density controls", async () => {
    const { container, cleanup } = render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    expect(container.querySelector('[data-testid="theme-toggle"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="theme-panel"]')).toBeNull();

    await act(async () => {
      container.querySelector<HTMLButtonElement>('[data-testid="theme-open-panel"]')!.click();
    });
    const panel = container.querySelector('[data-testid="theme-panel"]');
    expect(panel).toBeTruthy();
    expect(container.querySelector('[data-testid="theme-palette"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="theme-type"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="theme-mood"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="theme-density"]')).toBeTruthy();
    expect(panel!.textContent).toContain("Skins chrome/UI only");

    cleanup();
  });
});
