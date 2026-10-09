import { describe, expect, it } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import BigOStudio from "./BigOStudio";
import { matchRoute } from "../router";

describe("v2 Big O guest learner journey (Refs #204)", () => {
  it("has an explicit preview route and a no-signin entry screen", () => {
    expect(matchRoute("/v2")).toEqual({ name: "v2" });
    const { container, cleanup } = render(<BigOStudio />);
    expect(container.textContent).toContain("Big O");
    expect(container.textContent).toContain("No account");
    expect(container.querySelector('[data-testid="v2-start"]')).toBeTruthy();
    cleanup();
  });

  it("teaches terms before an algebra-linked interactive and supports back navigation", () => {
    const { container, cleanup } = render(<BigOStudio />);
    act(() => (container.querySelector('[data-testid="v2-start"]') as HTMLButtonElement).click());
    expect(container.querySelector('[data-testid="sticks-boxes-complexity"]')).toBeTruthy();
    expect(container.textContent).toContain("number of boxes");
    expect(container.textContent).toContain("exact count");
    expect(container.querySelector('[data-testid="v2-equation"]')?.textContent).toContain("W(3) = 3");
    expect(container.querySelector('[data-testid="v2-curve"]')).toBeTruthy();
    act(() => (container.querySelector('[data-testid="sticks-primary-btn"]') as HTMLButtonElement).click());
    expect(container.querySelector('[data-testid="v2-progress"]')?.textContent).toContain("1 of 3");
    act(() => (container.querySelector('[data-testid="v2-back"]') as HTMLButtonElement).click());
    expect(container.querySelector('[data-testid="v2-start"]')).toBeTruthy();
    cleanup();
  });

  it("requires an actual prediction instead of auto-completing the lesson", () => {
    const { container, cleanup } = render(<BigOStudio />);
    act(() => (container.querySelector('[data-testid="v2-start"]') as HTMLButtonElement).click());
    expect(container.querySelector('[data-testid="v2-check"]')?.hasAttribute("disabled")).toBe(true);
    expect(container.querySelector('[data-testid="v2-result"]')).toBeNull();
    cleanup();
  });
});
