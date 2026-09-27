import { afterEach, describe, expect, it, vi } from "vitest";
import { render } from "./test-utils";
import ErrorBoundary from "./ErrorBoundary";

function Boom(): never {
  throw new Error("boom");
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ErrorBoundary", () => {
  it("shows a recoverable card instead of a blank root", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    const { container, cleanup } = render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );
    expect(container.querySelector("[data-testid='render-error']")).toBeTruthy();
    expect(container.textContent).toContain("Something broke on this screen");
    expect(container.querySelector("[data-testid='render-error-retry']")).toBeTruthy();
    cleanup();
  });

  it("renders children when nothing throws", () => {
    const { container, cleanup } = render(
      <ErrorBoundary>
        <p>fine</p>
      </ErrorBoundary>,
    );
    expect(container.textContent).toBe("fine");
    cleanup();
  });
});