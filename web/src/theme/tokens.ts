/** Study OS design system — chrome/UI tokens only (Refs #165).
 *
 * Theme = { palette, appearance, type, mood, density }.
 * Out of scope: curated teach image assets + teacher pet/bot sprites.
 */

export type PaletteId = "lavender" | "slate" | "forest" | "sunset";
export type AppearanceId = "light" | "dark" | "system";
export type TypeId = "sans" | "serif" | "mono";
export type MoodId = "calm" | "focus" | "playful";
export type DensityId = "comfortable" | "compact" | "spacious";

export type ThemeConfig = {
  palette: PaletteId;
  appearance: AppearanceId;
  type: TypeId;
  mood: MoodId;
  density: DensityId;
};

export type ResolvedAppearance = "light" | "dark";

export const STORAGE_KEY = "sos.theme.v1";

/** Dark slate default — Pukujan hates bright lavender (Refs #165). */
export const DEFAULT_THEME: ThemeConfig = {
  palette: "slate",
  appearance: "dark",
  type: "sans",
  mood: "calm",
  density: "comfortable",
};

export const PALETTE_LABELS: Record<PaletteId, string> = {
  lavender: "Lavender",
  slate: "Slate",
  forest: "Forest",
  sunset: "Sunset",
};

export const TYPE_LABELS: Record<TypeId, string> = {
  sans: "Sans",
  serif: "Serif",
  mono: "Mono",
};

export const MOOD_LABELS: Record<MoodId, string> = {
  calm: "Calm",
  focus: "Focus",
  playful: "Playful",
};

export const DENSITY_LABELS: Record<DensityId, string> = {
  comfortable: "Comfortable",
  compact: "Compact",
  spacious: "Spacious",
};

export const APPEARANCE_LABELS: Record<AppearanceId, string> = {
  system: "System",
  light: "Light",
  dark: "Dark",
};

export function resolveAppearance(
  appearance: AppearanceId,
  prefersDark?: boolean,
): ResolvedAppearance {
  if (appearance === "light" || appearance === "dark") return appearance;
  if (typeof prefersDark === "boolean") return prefersDark ? "dark" : "light";
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  // Prefer dark when system preference is unknown (Pukujan / bright-lavender hate).
  return "dark";
}

export function parseStoredTheme(raw: string | null): ThemeConfig | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<ThemeConfig>;
    const theme: ThemeConfig = { ...DEFAULT_THEME };
    if (parsed.palette && parsed.palette in PALETTE_LABELS) theme.palette = parsed.palette;
    if (parsed.appearance && parsed.appearance in APPEARANCE_LABELS) {
      theme.appearance = parsed.appearance;
    }
    if (parsed.type && parsed.type in TYPE_LABELS) theme.type = parsed.type;
    if (parsed.mood && parsed.mood in MOOD_LABELS) theme.mood = parsed.mood;
    if (parsed.density && parsed.density in DENSITY_LABELS) theme.density = parsed.density;
    return theme;
  } catch {
    return null;
  }
}

/** Apply resolved theme axes onto documentElement for CSS selectors. */
export function applyThemeToDocument(
  theme: ThemeConfig,
  resolved: ResolvedAppearance,
  el: HTMLElement = document.documentElement,
): void {
  el.dataset.themePalette = theme.palette;
  el.dataset.themeAppearance = resolved;
  el.dataset.themeType = theme.type;
  el.dataset.themeMood = theme.mood;
  el.dataset.themeDensity = theme.density;
  el.style.colorScheme = resolved;
}

/** Sync boot script for index.html — keeps FOUC off before React mounts. */
export const THEME_BOOT_SCRIPT =
  '(function(){try{var k="sos.theme.v1";var d={palette:"slate",appearance:"dark",type:"sans",mood:"calm",density:"comfortable"};' +
  'var t=d;var r=localStorage.getItem(k);if(r){try{var p=JSON.parse(r);t=Object.assign({},d,p);}catch(e){}}' +
  'var a=t.appearance;var resolved=a==="light"||a==="dark"?a:(window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"dark");' +
  'var el=document.documentElement;el.dataset.themePalette=t.palette||d.palette;el.dataset.themeAppearance=resolved;' +
  'el.dataset.themeType=t.type||d.type;el.dataset.themeMood=t.mood||d.mood;el.dataset.themeDensity=t.density||d.density;' +
  'el.style.colorScheme=resolved;}catch(e){}})();';
