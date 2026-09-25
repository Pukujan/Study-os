import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import Pet from "./Pet";

function mockMatchMedia(matches = false) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }),
  });
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  mockMatchMedia(false);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("Pet free-roam", () => {
  it("renders floating full-body button with assistant label", () => {
    const { container, cleanup } = render(<Pet mood="idle" onTap={() => undefined} />);
    const btn = container.querySelector<HTMLButtonElement>("button[aria-label='Open study assistant']");
    expect(btn).toBeTruthy();
    expect(container.querySelector("[data-pet-float]")).toBeTruthy();
    expect(container.querySelector(".pet-sprite")).toBeTruthy();
    const sprite = container.querySelector<HTMLElement>(".pet-sprite");
    expect(sprite?.style.overflow).toBe("hidden");
    expect(Number.parseInt(sprite?.style.width || "0", 10)).toBeGreaterThan(60);
    cleanup();
  });

  it("shows coach tip after ~2s once per session and dismisses on hover", () => {
    vi.useFakeTimers();
    const { container, cleanup } = render(<Pet mood="idle" onTap={() => undefined} />);
    expect(container.querySelector(".pet-tip")).toBeNull();
    act(() => {
      vi.advanceTimersByTime(2100);
    });
    expect(container.querySelector(".pet-tip")?.textContent).toMatch(/Click me for assistant/i);
    const btn = container.querySelector<HTMLButtonElement>("button[aria-label='Open study assistant']");
    act(() => {
      btn?.focus();
      btn?.dispatchEvent(new FocusEvent("focus", { bubbles: true }));
    });
    expect(container.querySelector(".pet-tip")).toBeNull();
    expect(sessionStorage.getItem("sos.pet.tipSeen")).toBe("1");
    cleanup();
  });

  it("uses a low-prominence Hide control", () => {
    const { container, cleanup } = render(<Pet mood="idle" onTap={() => undefined} />);
    const hide = container.querySelector<HTMLButtonElement>("button[aria-label='Hide study buddy']");
    expect(hide?.textContent?.trim()).toBe("Hide");
    cleanup();
  });
});
