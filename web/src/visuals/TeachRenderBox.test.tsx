import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { act } from "react";
import Frame from "./Frame";
import TeachRenderBox, {
  PresentationIsland,
  listTeachRenderTypes,
  getTeachRenderer,
} from "./TeachRenderBox";
import { render } from "../test-utils";

describe("TeachRenderBox", () => {
  it("registers builtin island kinds including aliases", () => {
    const kinds = listTeachRenderTypes();
    for (const k of [
      "code_block",
      "mermaid",
      "mermaid_flow",
      "growth_workers",
      "growth_curve",
      "growth_table",
      "sticks_boxes_complexity",
      "interactive_ops_boxes",
    ]) {
      expect(kinds).toContain(k);
      expect(getTeachRenderer(k)).toBeTruthy();
    }
  });

  it("Frame mounts growth_table inside an island (SSR fallback)", () => {
    const html = renderToStaticMarkup(
      <Frame
        frame={{
          type: "growth_table",
          n_values: [2, 4, 8, 16],
          series: { label: "O(n)", values: [2, 4, 8, 16] },
        }}
      />,
    );
    expect(html).toContain('data-testid="teach-render-box"');
    expect(html).toContain('data-teach-render="growth_table"');
    expect(html).toContain("O(n)");
  });

  it("renders code_block and mermaid alias kinds", () => {
    const code = renderToStaticMarkup(
      <TeachRenderBox
        frame={{ type: "code_block", language: "python", source: "print(n)", caption: "snippet" }}
      />,
    );
    expect(code).toContain('data-teach-render="code_block"');
    expect(code).toContain("print(n)");

    const mermaid = renderToStaticMarkup(
      <TeachRenderBox
        frame={{ type: "mermaid", source: "flowchart TD\n  A-->B", caption: "flow" }}
      />,
    );
    expect(mermaid).toContain('data-teach-render="mermaid_flow"');
  });

  it("client mount uses shadow DOM isolation when attachShadow exists", () => {
    const { container, cleanup } = render(
      <PresentationIsland kind="code_block" label="x">
        <pre>hi</pre>
      </PresentationIsland>,
    );
    act(() => {
      // ref callback already ran during render
    });
    const host = container.querySelector('[data-testid="teach-render-box"]') as HTMLElement;
    expect(host).toBeTruthy();
    expect(host.getAttribute("data-isolation")).toBe("shadow-dom");
    expect(host.shadowRoot).toBeTruthy();
    expect(host.shadowRoot!.textContent).toContain("hi");
    expect(host.shadowRoot!.querySelector("[data-island-root]")).toBeTruthy();
    cleanup();
  });

  it("growth_workers and growth_curve mount as distinct island kinds", () => {
    const workers = renderToStaticMarkup(
      <Frame frame={{ type: "growth_workers", n_values: [2, 4], role_label: "workers" }} />,
    );
    expect(workers).toContain('data-teach-render="growth_workers"');
    const curve = renderToStaticMarkup(
      <Frame
        frame={{
          type: "growth_curve",
          n_values: [2, 4],
          series: { label: "fast", values: [1, 8] },
        }}
      />,
    );
    expect(curve).toContain('data-teach-render="growth_curve"');
  });

  it("sticks_boxes_complexity mounts as its own island kind", () => {
    const html = renderToStaticMarkup(
      <Frame
        frame={{
          type: "sticks_boxes_complexity",
          initial_complexity: "O(1)",
          initial_n: 2,
        }}
      />,
    );
    expect(html).toContain('data-teach-render="sticks_boxes_complexity"');
    expect(html).toContain("Put Next Stick");
  });

  it("returns null for undefined / untyped frames (Explain-again harden)", () => {
    const { container, cleanup } = render(<TeachRenderBox frame={undefined as never} />);
    expect(container.querySelector('[data-testid="teach-render-box"]')).toBeNull();
    cleanup();
    const again = render(<TeachRenderBox frame={{} as never} />);
    expect(again.container.querySelector('[data-testid="teach-render-box"]')).toBeNull();
    again.cleanup();
  });

});
