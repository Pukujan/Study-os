// Minimal, safe markdown renderer: no raw HTML, charts in fenced blocks stay monospace.
import { Fragment, type ReactNode } from "react";

export type Block =
  | { type: "code"; lang: string; text: string }
  | { type: "heading"; level: number; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "para"; text: string };

export function parseBlocks(src: string): Block[] {
  const lines = (src || "").replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const fence = line.match(/^```(\w*)\s*$/);
    if (fence) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```\s*$/.test(lines[i])) buf.push(lines[i++]);
      i++; // closing fence
      blocks.push({ type: "code", lang: fence[1] || "text", text: buf.join("\n") });
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      blocks.push({ type: "heading", level: heading[1].length, text: heading[2] });
      i++;
      continue;
    }
    if (/^\s*([-*]|\d+[.)])\s+/.test(line)) {
      const ordered = /^\s*\d+[.)]\s+/.test(line);
      const items: string[] = [];
      while (i < lines.length && /^\s*([-*]|\d+[.)])\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*]|\d+[.)])\s+/, ""));
        i++;
      }
      blocks.push({ type: "list", ordered, items });
      continue;
    }
    if (line.trim() === "") {
      i++;
      continue;
    }
    const buf: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^```/.test(lines[i]) && !/^#{1,4}\s/.test(lines[i]) && !/^\s*([-*]|\d+[.)])\s+/.test(lines[i])) {
      buf.push(lines[i++]);
    }
    blocks.push({ type: "para", text: buf.join("\n") });
  }
  return blocks;
}

export function renderInline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g;
  let last = 0;
  let key = 0;
  for (const m of text.matchAll(re)) {
    const idx = m.index ?? 0;
    if (idx > last) out.push(text.slice(last, idx));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(<strong key={key++}>{renderInline(tok.slice(2, -2))}</strong>);
    else if (tok.startsWith("`")) out.push(<code key={key++}>{tok.slice(1, -1)}</code>);
    else out.push(<em key={key++}>{tok.slice(1, -1)}</em>);
    last = idx + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out.map((n, j) => (typeof n === "string" ? <Fragment key={`t${j}`}>{withBreaks(n)}</Fragment> : n));
}

function withBreaks(s: string): ReactNode[] {
  const parts = s.split("\n");
  return parts.flatMap((p, i) => (i === 0 ? [p] : [<br key={i} />, p]));
}

export function Markdown({ text }: { text: string }) {
  return (
    <div className="md">
      {parseBlocks(text).map((b, i) => {
        switch (b.type) {
          case "code":
            return (
              <pre key={i} className={`chart lang-${b.lang}`} aria-label="chart">
                {b.text}
              </pre>
            );
          case "heading": {
            const Tag = (`h${Math.min(b.level + 1, 6)}` as unknown) as "h3";
            return <Tag key={i}>{renderInline(b.text)}</Tag>;
          }
          case "list": {
            const items = b.items.map((it, j) => <li key={j}>{renderInline(it)}</li>);
            return b.ordered ? <ol key={i}>{items}</ol> : <ul key={i}>{items}</ul>;
          }
          default:
            return <p key={i}>{renderInline(b.text)}</p>;
        }
      })}
    </div>
  );
}

/** Remove a trailing numbered option list (the choices are rendered as buttons instead). */
export function stripChoiceList(md: string): string {
  const lines = (md || "").replace(/\s+$/, "").split("\n");
  let end = lines.length;
  while (end > 0 && /^\s*\d+[.)]\s+/.test(lines[end - 1])) end--;
  if (end === lines.length) return md;
  return lines.slice(0, end).join("\n").replace(/\s+$/, "");
}
