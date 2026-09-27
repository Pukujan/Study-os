import { useEffect, useId, useRef, useState } from "react";
import { useTheme } from "./ThemeProvider";
import {
  APPEARANCE_LABELS,
  DENSITY_LABELS,
  MOOD_LABELS,
  PALETTE_LABELS,
  TYPE_LABELS,
  type AppearanceId,
  type DensityId,
  type MoodId,
  type PaletteId,
  type TypeId,
} from "./tokens";

/** Chrome-only theme controls. Does not restyle teach images or pet/bot. */
export default function ThemeToggle() {
  const {
    theme,
    resolvedAppearance,
    setPalette,
    setAppearance,
    setType,
    setMood,
    setDensity,
    toggleAppearance,
  } = useTheme();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="theme-toggle" ref={rootRef} data-testid="theme-toggle">
      <button
        type="button"
        className="btn small theme-toggle-quick"
        onClick={toggleAppearance}
        data-track="theme.toggle-appearance"
        data-testid="theme-appearance-toggle"
        aria-label={`Switch to ${resolvedAppearance === "dark" ? "light" : "dark"} appearance`}
        title={`Appearance: ${resolvedAppearance} (click to toggle)`}
      >
        {resolvedAppearance === "dark" ? "Dark" : "Light"}
      </button>
      <button
        type="button"
        className="btn small theme-toggle-open"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        data-track="theme.open-panel"
        data-testid="theme-open-panel"
      >
        Theme
      </button>
      {open && (
        <div
          id={panelId}
          className="theme-panel card"
          role="dialog"
          aria-label="Design system"
          data-testid="theme-panel"
        >
          <fieldset className="theme-fieldset">
            <legend>Appearance</legend>
            <select
              value={theme.appearance}
              onChange={(e) => setAppearance(e.target.value as AppearanceId)}
              data-testid="theme-appearance"
              aria-label="Appearance"
            >
              {(Object.keys(APPEARANCE_LABELS) as AppearanceId[]).map((id) => (
                <option key={id} value={id}>
                  {APPEARANCE_LABELS[id]}
                </option>
              ))}
            </select>
          </fieldset>
          <fieldset className="theme-fieldset">
            <legend>Palette</legend>
            <select
              value={theme.palette}
              onChange={(e) => setPalette(e.target.value as PaletteId)}
              data-testid="theme-palette"
              aria-label="Color palette"
            >
              {(Object.keys(PALETTE_LABELS) as PaletteId[]).map((id) => (
                <option key={id} value={id}>
                  {PALETTE_LABELS[id]}
                </option>
              ))}
            </select>
          </fieldset>
          <fieldset className="theme-fieldset">
            <legend>Type</legend>
            <select
              value={theme.type}
              onChange={(e) => setType(e.target.value as TypeId)}
              data-testid="theme-type"
              aria-label="Typography"
            >
              {(Object.keys(TYPE_LABELS) as TypeId[]).map((id) => (
                <option key={id} value={id}>
                  {TYPE_LABELS[id]}
                </option>
              ))}
            </select>
          </fieldset>
          <fieldset className="theme-fieldset">
            <legend>Mood</legend>
            <select
              value={theme.mood}
              onChange={(e) => setMood(e.target.value as MoodId)}
              data-testid="theme-mood"
              aria-label="Mood"
            >
              {(Object.keys(MOOD_LABELS) as MoodId[]).map((id) => (
                <option key={id} value={id}>
                  {MOOD_LABELS[id]}
                </option>
              ))}
            </select>
          </fieldset>
          <fieldset className="theme-fieldset">
            <legend>Density</legend>
            <select
              value={theme.density}
              onChange={(e) => setDensity(e.target.value as DensityId)}
              data-testid="theme-density"
              aria-label="Density"
            >
              {(Object.keys(DENSITY_LABELS) as DensityId[]).map((id) => (
                <option key={id} value={id}>
                  {DENSITY_LABELS[id]}
                </option>
              ))}
            </select>
          </fieldset>
          <p className="fine theme-panel-note">
            Skins chrome/UI only — teach images &amp; pet stay as-is.
          </p>
        </div>
      )}
    </div>
  );
}
