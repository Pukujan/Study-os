import { useState, type ReactNode } from "react";
import type { CodeTreeFrame, CodeTreeNode as NodeType } from "../api";

function TreeNode({ node, depth }: { node: NodeType; depth: number }) {
  const [open, setOpen] = useState(true);
  const hasChildren = node.children && node.children.length > 0;
  return (
    <li style={{ marginLeft: depth > 0 ? "1rem" : 0 }}>
      {hasChildren ? (
        <details open={open} onToggle={(e) => setOpen(e.currentTarget.open)}>
          <summary className="code-tree-summary" aria-expanded={open}>
            {node.label}
          </summary>
          <ul className="code-tree-children" role="group">
            {node.children!.map((child, i) => (
              <TreeNode key={i} node={child} depth={depth + 1} />
            ))}
          </ul>
        </details>
      ) : (
        <span className="code-tree-leaf">{node.label}</span>
      )}
    </li>
  );
}

export function describeCodeTree(frame: CodeTreeFrame): string {
  let desc = `Code tree with ${frame.lines.length} lines`;
  if (frame.highlight && frame.highlight.length > 0) desc += `, highlights on lines ${frame.highlight.join(", ")}`;
  if (frame.underlines && frame.underlines.length > 0) desc += `, ${frame.underlines.length} underlined ranges`;
  if (frame.tree) desc += `, tree: ${frame.tree.label}`;
  return desc;
}

export default function CodeTree({ frame }: { frame: CodeTreeFrame }) {
  const highlightSet = new Set(frame.highlight ?? []);
  const underlinesByLine = new Map<number, { span: [number, number]; label?: string }[]>();
  for (const u of frame.underlines ?? []) {
    const list = underlinesByLine.get(u.line) ?? [];
    list.push(u);
    underlinesByLine.set(u.line, list);
  }

  function renderLine(line: string, underlines: { span: [number, number]; label?: string }[]): ReactNode {
    if (underlines.length === 0) return line;
    const segments: { start: number; end: number; label?: string }[] = [];
    let pos = 0;
    for (const u of [...underlines].sort((a, b) => a.span[0] - b.span[0])) {
      if (u.span[0] > pos) segments.push({ start: pos, end: u.span[0] });
      segments.push({ start: u.span[0], end: u.span[1], label: u.label });
      pos = u.span[1];
    }
    if (pos < line.length) segments.push({ start: pos, end: line.length });
    return (
      <>
        {segments.map((s, i) =>
          s.label ? (
            <span key={i} className="code-tree-underline-wrapper" title={s.label}>
              <span className="code-tree-underline">{line.slice(s.start, s.end)}</span>
              <span className="code-tree-underline-label">{s.label}</span>
            </span>
          ) : (
            <span key={i}>{line.slice(s.start, s.end)}</span>
          )
        )}
      </>
    );
  }

  return (
    <figure className="code-tree">
      <pre className="code-tree-code">
        <code>
          {frame.lines.map((line, i) => {
            const underlines = underlinesByLine.get(i) ?? [];
            const highlighted = highlightSet.has(i);
            const content = renderLine(line, underlines);
            return (
              <div key={i} className={`code-tree-line${highlighted ? " highlighted" : ""}`}>
                {content}
              </div>
            );
          })}
        </code>
      </pre>
      {frame.tree && (
        <ul className="code-tree-root" aria-label="Code structure tree">
          <TreeNode node={frame.tree} depth={0} />
        </ul>
      )}
      {frame.caption && <figcaption className="frame-caption">{frame.caption}</figcaption>}
    </figure>
  );
}
