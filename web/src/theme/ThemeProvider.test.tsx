import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { ThemeProvider, useTheme } from "./ThemeProvider";
import { STORAGE_KEY } from "./tokens";
import { render } from "../test-utils";

function Probe() {
  const { theme, resolvedAppearance, setPalette, toggleAppearance, setAppearance } = useTheme();
  return (
    <div>
      <span data-testid="palette">{theme.palette}</span>
      <span data-testid="appearance">{resolvedAppearance}</span>
      <button type="button" data-testid="to-forest" onClick={() => setPalette("forest")}>
        forest
      </button>
      <button type="button" data-testid="toggle" onClick={toggleAppearance}>
        toggle
      </button>
      <button type="button" data-testid="to-light" onClick={() => setAppearance("light")}>
        light
      </button>
    </div>
  );
}

describe("ThemeProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme-palette");
    document.documentElement.removeAttribute("data-theme-appearance");
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("applies dark default, persists palette, and toggles appearance", async () => {
    const { container, cleanup } = render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );

    expect(container.querySelector('[data-testid="appearance"]')?.textContent).toBe("dark");
    expect(container.querySelector('[data-testid="palette"]')?.textContent).toBe("slate");
    expect(document.documentElement.dataset.themeAppearance).toBe("dark");
    expect(document.documentElement.dataset.themePalette).toBe("slate");

    await act(async () => {
      container.querySelector<HTMLButtonElement>('[data-testid="to-forest"]')!.click();
    });
    expect(container.querySelector('[data-testid="palette"]')?.textContent).toBe("forest");
    expect(document.documentElement.dataset.themePalette).toBe("forest");
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
    expect(stored.palette).toBe("forest");

    await act(async () => {
      container.querySelector<HTMLButtonElement>('[data-testid="toggle"]')!.click();
    });
    expect(container.querySelector('[data-testid="appearance"]')?.textContent).toBe("light");
    expect(document.documentElement.dataset.themeAppearance).toBe("light");

    cleanup();
  });
});
