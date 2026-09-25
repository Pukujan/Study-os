import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

let mermaidReady = false;

function initMermaid() {
  if (mermaidReady) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    securityLevel: "loose",
    themeVariables: {
      fontSize: "16px",
      primaryColor: "#F4F1FF",
      primaryTextColor: "#111B4D",
      primaryBorderColor: "#8F7CFF",
      lineColor: "#111B4D",
    },
  });
  mermaidReady = true;
}

function getEffectiveDirection(direction: "TD" | "LR" | undefined, narrow: boolean): "TD" | "LR" {
  if (narrow) return "TD";
  return direction ?? "TD";
}

function rewriteDirection(source: string, direction: "TD" | "LR"): string {
  const lines = source.split("\n");
  if (lines.length === 0) return source;
  const first = lines[0].replace(/^\s*/, "");
  const match = first.match(/^(flowchart|graph)\s+(TD|LR|BT|RL)\b/i);
  if (match) {
    lines[0] = `${match[1]} ${direction}`;
  }
  return lines.join("\n");
}

function extractNodeId(line: string): string | null {
  const trimmed = line.trim();
  // Node definitions: A[...], A(...), A{...}, A[/.../], A{{...}}, A[...]
  const m = trimmed.match(/^([A-Za-z0-9_]+)\s*(\[|\(|\{|\/)/);
  if (m) return m[1];
  return null;
}

function extractEdgeIds(line: string): string[] {
  const ids: string[] = [];
  const parts = line.split(/\s*(?:-->|--|\.-|-\.|==>|==|\.=|=\.|~~>|~~|\.-\.-|==|~~)\s*/);
  for (const part of parts) {
    const id = extractNodeId(part);
    if (id) ids.push(id);
  }
  return ids;
}

function filterSource(source: string, revealed: string[] | undefined): string {
  if (!revealed || revealed.length === 0) return source;
  const revealedSet = new Set(revealed);
  const out: string[] = [];
  for (const line of source.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) {
      out.push(line);
      continue;
    }
    const nodeId = extractNodeId(line);
    if (nodeId) {
      if (revealedSet.has(nodeId)) out.push(line);
      continue;
    }
    if (/\s*(?:-->|--|\.\.-|-\.-|==>|==|\.==|==\.|~~>|~~|~~\.|~~)\s*/.test(line)) {
      const ids = extractEdgeIds(line);
      if (ids.every((id) => revealedSet.has(id))) out.push(line);
      continue;
    }
    // Keep directives, classDef, subgraph, etc.
    out.push(line);
  }
  return out.join("\n");
}

type MermaidDiagramProps = {
  source: string;
  revealedNodes?: string[];
  direction?: "TD" | "LR";
  zoomPan?: boolean;
  className?: string;
  caption?: string;
};

export default function MermaidDiagram({
  source,
  revealedNodes,
  direction,
  zoomPan = true,
  className = "",
  caption,
}: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef({ startX: 0, startY: 0, panX: 0, panY: 0 });
  const [narrow, setNarrow] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const update = () => setNarrow(window.innerWidth < 720);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  useEffect(() => {
    initMermaid();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const effectiveDir = getEffectiveDirection(direction, narrow);
    const filtered = filterSource(rewriteDirection(source, effectiveDir), revealedNodes);
    const id = `mmd-${Math.random().toString(36).slice(2, 11)}`;
    let cancelled = false;
    mermaid
      .render(id, filtered)
      .then(({ svg }) => {
        if (!cancelled) {
          setSvg(svg);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to render diagram");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [source, revealedNodes, direction, narrow]);

  const handlePointerDown = (e: React.PointerEvent) => {
    if (!zoomPan) return;
    setDragging(true);
    dragRef.current = { startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragging) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    setPan({ x: dragRef.current.panX + dx, y: dragRef.current.panY + dy });
  };

  const handlePointerUp = () => {
    setDragging(false);
  };

  const reset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const wrapper = (
    <div
      ref={containerRef}
      className={`mermaid-diagram ${className}`}
      role="img"
      aria-label={caption || "Diagram"}
      style={{ cursor: dragging ? "grabbing" : zoomPan ? "grab" : "default" }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      {svg ? (
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "top left",
          }}
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      ) : error ? (
        <div className="mermaid-error" role="alert">
          {error}
        </div>
      ) : (
        <div className="mermaid-loading">Loading diagram…</div>
      )}
    </div>
  );

  const controls = zoomPan && (
    <div className="mermaid-controls" role="group" aria-label="Diagram zoom">
      <button className="btn small" onClick={() => setZoom((z) => Math.min(z + 0.25, 3))} aria-label="Zoom in">
        Zoom in
      </button>
      <button className="btn small" onClick={() => setZoom((z) => Math.max(z - 0.25, 0.5))} aria-label="Zoom out">
        Zoom out
      </button>
      <button className="btn small" onClick={reset} aria-label="Reset zoom and pan">
        Reset
      </button>
    </div>
  );

  return (
    <>
      {wrapper}
      {controls}
    </>
  );
}
