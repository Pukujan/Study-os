import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import Sprite from "./Sprite";

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
  mockMatchMedia(false);
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("Sprite held-pose (A22a)", () => {
  it("advances discrete frames at low fps with no CSS animation", () => {
    const { container, cleanup } = render(
      <Sprite src="/mascot/pet-idle.webp" frames={6} frameW={144} frameH={176} height={88} fps={2} loop />,
    );
    const el = container.querySelector<HTMLElement>('[data-testid="mascot.sprite"]');
    expect(el).toBeTruthy();
    expect(el?.getAttribute("data-anim")).toBe("held-pose");
    expect(el?.getAttribute("data-fps")).toBe("2");
    expect(el?.getAttribute("data-frame")).toBe("0");
    expect(el?.style.animation).toMatch(/none|^$/);

    act(() => {
      vi.advanceTimersByTime(500);
    });
    // 2 fps => 500ms per hold; after 500ms should be frame 1
    expect(el?.getAttribute("data-frame")).toBe("1");

    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(el?.getAttribute("data-frame")).toBe("2");
    cleanup();
  });

  it("holds last frame and fires onEnd once for one-shots", () => {
    const onEnd = vi.fn();
    const { container, cleanup } = render(
      <Sprite
        src="/mascot/pet-ball.webp"
        frames={3}
        frameW={144}
        frameH={176}
        height={88}
        fps={2}
        loop={false}
        onEnd={onEnd}
      />,
    );
    const el = container.querySelector<HTMLElement>('[data-testid="mascot.sprite"]');
    act(() => {
      vi.advanceTimersByTime(500); // 0 -> 1
      vi.advanceTimersByTime(500); // 1 -> 2 (last visible)
      vi.advanceTimersByTime(500); // attempt past end -> onEnd, hold 2
    });
    expect(el?.getAttribute("data-frame")).toBe("2");
    expect(onEnd).toHaveBeenCalledTimes(1);
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(onEnd).toHaveBeenCalledTimes(1);
    cleanup();
  });

  it("stays on frame 0 when paused", () => {
    const { container, cleanup } = render(
      <Sprite src="/mascot/pet-idle.webp" frames={6} frameW={144} frameH={176} fps={4} loop paused />,
    );
    const el = container.querySelector<HTMLElement>('[data-testid="mascot.sprite"]');
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(el?.getAttribute("data-frame")).toBe("0");
    cleanup();
  });
});
