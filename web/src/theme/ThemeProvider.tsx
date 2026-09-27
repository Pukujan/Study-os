import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { tracker } from "../tracker";
import {
  DEFAULT_THEME,
  STORAGE_KEY,
  applyThemeToDocument,
  parseStoredTheme,
  resolveAppearance,
  type AppearanceId,
  type DensityId,
  type MoodId,
  type PaletteId,
  type ResolvedAppearance,
  type ThemeConfig,
  type TypeId,
} from "./tokens";

type ThemeContextValue = {
  theme: ThemeConfig;
  resolvedAppearance: ResolvedAppearance;
  setTheme: (patch: Partial<ThemeConfig>) => void;
  setPalette: (palette: PaletteId) => void;
  setAppearance: (appearance: AppearanceId) => void;
  setType: (type: TypeId) => void;
  setMood: (mood: MoodId) => void;
  setDensity: (density: DensityId) => void;
  toggleAppearance: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function readInitial(): ThemeConfig {
  if (typeof window === "undefined") return DEFAULT_THEME;
  return parseStoredTheme(localStorage.getItem(STORAGE_KEY)) ?? DEFAULT_THEME;
}

function logPreferDark(resolved: ResolvedAppearance): void {
  tracker.track({
    type: "rating",
    control: "prefer_dark",
    value_int: resolved === "dark" ? 1 : 0,
  });
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeConfig>(readInitial);
  const [systemDark, setSystemDark] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) return true;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const loggedInitial = useRef(false);

  const resolvedAppearance = useMemo(
    () => resolveAppearance(theme.appearance, systemDark),
    [theme.appearance, systemDark],
  );

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setSystemDark(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    applyThemeToDocument(theme, resolvedAppearance);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(theme));
    } catch {
      /* ignore quota / private mode */
    }
    if (!loggedInitial.current) {
      loggedInitial.current = true;
      logPreferDark(resolvedAppearance);
    }
  }, [theme, resolvedAppearance]);

  const setTheme = useCallback((patch: Partial<ThemeConfig>) => {
    setThemeState((prev) => {
      const next = { ...prev, ...patch };
      if (patch.appearance !== undefined) {
        const resolved = resolveAppearance(next.appearance, systemDark);
        logPreferDark(resolved);
      }
      return next;
    });
  }, [systemDark]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedAppearance,
      setTheme,
      setPalette: (palette) => setTheme({ palette }),
      setAppearance: (appearance) => setTheme({ appearance }),
      setType: (type) => setTheme({ type }),
      setMood: (mood) => setTheme({ mood }),
      setDensity: (density) => setTheme({ density }),
      toggleAppearance: () =>
        setThemeState((prev) => {
          const current = resolveAppearance(prev.appearance, systemDark);
          const nextAppearance: AppearanceId = current === "dark" ? "light" : "dark";
          logPreferDark(nextAppearance);
          return { ...prev, appearance: nextAppearance };
        }),
    }),
    [theme, resolvedAppearance, setTheme, systemDark],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
