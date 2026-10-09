import { describe, expect, it } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import BigOStudio from "./BigOStudio";
import { matchRoute } from "../router";

function click(container: HTMLElement, testid: string) {
  const button = container.querySelector<HTMLButtonElement>(`[data-testid="${testid}"]`);
  if (!button) throw new Error("Missing button: " + testid);
  act(() => button.click());
}

describe("v2 Big O learner journey (#204)", () => {
  it("is a public React route with a no-signin game entry", () => {
    expect(matchRoute("/v2")).toEqual({ name: "v2" });
    const { container, cleanup } = render(<BigOStudio />);
    expect(container.textContent).toContain("No account");
    expect(container.querySelector('[data-testid="v2-start"]')).not.toBeNull();
    cleanup();
  });

  it("computer picks the mission; every move updates a side-by-side graph", () => {
    const { container, cleanup } = render(<BigOStudio />);
    click(container, "v2-start");
    expect(container.querySelector('[data-testid="sticks-complexity-select"]')).toBeNull();
    expect(container.querySelector('[data-testid="v2-equation"]')).toBeNull();
    expect(container.querySelector('[data-testid="v2-curve"]')?.getAttribute("data-live-work")).toBe("0");

    click(container, "v2-stick");
    click(container, "v2-target-box:0");
    expect(container.querySelector('[data-testid="v2-live-work"]')?.textContent).toContain("1 step");
    expect(container.querySelector('[data-testid="v2-curve"]')?.getAttribute("data-live-work")).toBe("1");
    expect(container.querySelector('[data-testid="v2-equation"]')).toBeNull();

    click(container, "v2-stick");
    click(container, "v2-target-box:0");
    expect(container.querySelector('[data-testid="v2-growth-game"]')?.getAttribute("data-placed")).toBe("1");
    expect(container.querySelector('[data-testid="v2-game-feedback"]')?.textContent).toContain("Already filled");

    click(container, "v2-stick");
    click(container, "v2-target-box:1");
    click(container, "v2-stick");
    click(container, "v2-target-box:2");

    expect(container.querySelector('[data-testid="v2-growth-game"]')?.getAttribute("data-complete")).toBe("true");
    expect(container.querySelector('[data-testid="v2-rule-reveal"]')?.textContent).toContain("O(n)");
    expect(container.querySelector('[data-testid="v2-equation"]')?.textContent).toContain("W(3) = 3");
    click(container, "v2-next");
    expect(container.querySelector('[data-testid="v2-growth-game"]')?.getAttribute("data-mission")).toBe("cover-four");
    expect(container.querySelector('[data-testid="v2-graph-caption"]')?.textContent).toContain("0 work");
    cleanup();
  });

  it("restores the physical board and graph together after overview navigation", () => {
    const { container, cleanup } = render(<BigOStudio />);
    click(container, "v2-start");
    click(container, "v2-stick");
    click(container, "v2-target-box:1");
    click(container, "v2-back");
    click(container, "v2-start");
    expect(container.querySelector('[data-testid="v2-growth-game"]')?.getAttribute("data-placed")).toBe("1");
    expect(container.querySelector('[data-testid="v2-target-box:1"]')?.getAttribute("data-filled")).toBe("true");
    expect(container.querySelector('[data-testid="v2-curve"]')?.getAttribute("data-live-work")).toBe("1");
    cleanup();
  });
});
