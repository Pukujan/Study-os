import { describe, expect, it } from "vitest";
import {
  DEFAULT_THEME,
  STORAGE_KEY,
  applyThemeToDocument,
  parseStoredTheme,
  resolveAppearance,
} from "./tokens";

describe("design tokens (Refs #165)", () => {
  it("defaults to dark slate (not bright lavender)", () => {
    expect(DEFAULT_THEME.appearance).toBe("dark");
    expect(DEFAULT_THEME.palette).toBe("slate");
    expect(STORAGE_KEY).toBe("sos.theme.v1");
  });

  it("resolveAppearance honors explicit light/dark and prefers dark for system unknown", () => {
    expect(resolveAppearance("light")).toBe("light");
    expect(resolveAppearance("dark")).toBe("dark");
    expect(resolveAppearance("system", true)).toBe("dark");
    expect(resolveAppearance("system", false)).toBe("light");
  });

  it("parseStoredTheme merges valid axes and ignores junk", () => {
    expect(parseStoredTheme(null)).toBeNull();
    expect(parseStoredTheme("{not json")).toBeNull();
    const parsed = parseStoredTheme(
      JSON.stringify({ palette: "forest", appearance: "light", type: "serif", mood: "playful", density: "compact", extra: 1 }),
    );
    expect(parsed).toEqual({
      palette: "forest",
      appearance: "light",
      type: "serif",
      mood: "playful",
      density: "compact",
    });
    const bad = parseStoredTheme(JSON.stringify({ palette: "neon", appearance: "sepia" }));
    expect(bad?.palette).toBe(DEFAULT_THEME.palette);
    expect(bad?.appearance).toBe(DEFAULT_THEME.appearance);
  });

  it("applyThemeToDocument sets data attributes and color-scheme", () => {
    const el = document.createElement("div");
    applyThemeToDocument(
      { palette: "sunset", appearance: "dark", type: "mono", mood: "focus", density: "spacious" },
      "dark",
      el,
    );
    expect(el.dataset.themePalette).toBe("sunset");
    expect(el.dataset.themeAppearance).toBe("dark");
    expect(el.dataset.themeType).toBe("mono");
    expect(el.dataset.themeMood).toBe("focus");
    expect(el.dataset.themeDensity).toBe("spacious");
    expect(el.style.colorScheme).toBe("dark");
  });
});
