import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { Markdown, parseBlocks } from "./markdown";

describe("markdown", () => {
  it("keeps chart blocks verbatim and monospace", () => {
    const md = "Look:\n\n```text\npositions(p):  1   2\nnumbers(a):    4   7\n```\n\n**What is `p`?**";
    const blocks = parseBlocks(md);
    expect(blocks.map((b) => b.type)).toEqual(["para", "code", "para"]);
    const html = renderToStaticMarkup(<Markdown text={md} />);
    expect(html).toContain('<pre class="chart lang-text"');
    expect(html).toContain("positions(p):  1   2");
    expect(html).toContain("<strong>What is `p`?</strong>");
  });

  it("escapes raw html", () => {
    const html = renderToStaticMarkup(<Markdown text={"<img src=x onerror=alert(1)> hi"} />);
    expect(html).not.toContain("<img");
    expect(html).toContain("&lt;img");
  });

  it("renders lists and inline code", () => {
    const html = renderToStaticMarkup(<Markdown text={"1. one `a`\n2. two\n\n- x\n- *y*"} />);
    expect(html).toContain("<ol><li>one <code>a</code></li><li>two</li></ol>");
    expect(html).toContain("<ul><li>x</li><li><em>y</em></li></ul>");
  });
});
