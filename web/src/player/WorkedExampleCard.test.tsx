import { describe, expect, it } from "vitest";
import type { WorkedExample } from "../api";
import { render } from "../test-utils";
import WorkedExampleCard from "./WorkedExampleCard";

const loose = (value: unknown) => value as WorkedExample;

describe("WorkedExampleCard", () => {
  it("renders md content", () => {
    const { container, cleanup } = render(<WorkedExampleCard example={{ md: "Solve 1 + 2." }} />);
    expect(container.textContent).toContain("Solve 1 + 2.");
    cleanup();
  });

  it("renders a stripped payload without throwing", () => {
    const { container, cleanup } = render(<WorkedExampleCard example={loose({ frames: [] })} />);
    expect(container.querySelector("[data-testid='worked-example']")).toBeTruthy();
    expect(container.querySelector("[data-testid='worked-example-empty']")).toBeTruthy();
    cleanup();
  });

  it("still renders frames when there is no text", () => {
    const example = loose({
      frames: [{ type: "box_index", array: [4, 7, 2], show_positions: true, show_indices: false }],
    });
    const { container, cleanup } = render(<WorkedExampleCard example={example} />);
    expect(container.querySelector("[data-testid='worked-example']")).toBeTruthy();
    expect(container.querySelector("[data-testid='worked-example-empty']")).toBeNull();
    cleanup();
  });
});