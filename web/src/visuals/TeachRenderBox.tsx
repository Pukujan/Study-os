/**
 * TeachRenderBox / PresentationIsland — ChatGPT-style visual island.
 *
 * Isolation: open Shadow DOM when available (global app CSS cannot pierce
 * into tables / pre / svg). Falls back to CSS-module scoped light DOM for SSR
 * and environments without attachShadow. Island styles ship as a CSS module
 * and are injected into the shadow root as text.
 *
 * New render types: registerTeachRender({ types, describe, render }) then
 * add the Frame union member in api.ts.
 */
import {
  useCallback,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import type {
  BoxIndexFrame,
  CodeBlockFrame,
  CodeTreeFrame,
  FractionBarFrame,
  Frame as FrameType,
  GrowthCurveFrame,
  GrowthTableFrame,
  GrowthWorkersFrame,
  MermaidFlowFrame,
  SticksBoxesComplexityFrame,
} from "../api";
import FractionBar, { describeFractionBar } from "./FractionBar";
import NumberLine from "./NumberLine";
import BoxIndex, { describeBoxIndex } from "./BoxIndex";
import MermaidDiagram from "./MermaidDiagram";
import CodeTree, { describeCodeTree } from "./CodeTree";
import GrowthTable, { describeGrowthTable } from "./GrowthTable";
import GrowthWorkers, { describeGrowthWorkers } from "./GrowthWorkers";
import GrowthCurve, { describeGrowthCurve } from "./GrowthCurve";
import SticksBoxesComplexity, { describeSticksBoxesComplexity } from "./SticksBoxesComplexity";
import styles from "./TeachRenderBox.module.css";
import islandCss from "./TeachRenderBox.module.css?inline";
import {
  canonicalTeachRenderType,
  getTeachRenderer,
  registerTeachRender,
  listTeachRenderTypes,
  type TeachRenderType,
} from "./teachRenderRegistry";

export type { TeachRenderType };
export { registerTeachRender, getTeachRenderer, listTeachRenderTypes };

type IslandProps = {
  kind: TeachRenderType | string;
  label?: string;
  children: ReactNode;
  caption?: string | null;
  className?: string;
  style?: CSSProperties;
};

function IslandBody({
  kind,
  children,
  caption,
  className,
}: {
  kind: string;
  children: ReactNode;
  caption?: string | null;
  className?: string;
}) {
  const cls = [styles.island, className].filter(Boolean).join(" ");
  return (
    <div className={cls} data-teach-kind={kind}>
      {children}
      {caption ? <figcaption className={styles.caption}>{caption}</figcaption> : null}
    </div>
  );
}

/**
 * Scoped shell. Prefer Shadow DOM; CSS modules still apply inside the island
 * (and as the SSR / no-shadow fallback).
 */
export function PresentationIsland({ kind, label, children, caption, className, style }: IslandProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [shadowMount, setShadowMount] = useState<HTMLElement | null>(null);

  const attach = useCallback((node: HTMLDivElement | null) => {
    hostRef.current = node;
    if (!node) {
      setShadowMount(null);
      return;
    }
    if (typeof node.attachShadow !== "function") {
      setShadowMount(null);
      return;
    }
    const shadow = node.shadowRoot ?? node.attachShadow({ mode: "open" });
    if (!shadow.querySelector("style[data-teach-island]")) {
      const styleEl = document.createElement("style");
      styleEl.setAttribute("data-teach-island", "");
      styleEl.textContent = islandCss;
      shadow.appendChild(styleEl);
    }
    let root = shadow.querySelector("[data-island-root]") as HTMLElement | null;
    if (!root) {
      root = document.createElement("div");
      root.setAttribute("data-island-root", "");
      shadow.appendChild(root);
    }
    setShadowMount(root);
  }, []);

  useLayoutEffect(() => {
    if (hostRef.current && !shadowMount) attach(hostRef.current);
  }, [attach, shadowMount]);

  const body = (
    <IslandBody kind={kind} caption={caption} className={className}>
      {children}
    </IslandBody>
  );

  const isolation = shadowMount ? "shadow-dom" : "css-module";

  // Host must be a shadow-capable element (div). <figure> cannot attachShadow in browsers/jsdom.
  return (
    <div
      ref={attach}
      role="figure"
      className={shadowMount ? undefined : styles.fallbackHost}
      data-teach-render={kind}
      data-testid="teach-render-box"
      data-isolation={isolation}
      aria-label={label || undefined}
      style={style}
    >
      {shadowMount ? createPortal(body, shadowMount) : body}
    </div>
  );
}

function CodeBlockView({ frame }: { frame: CodeBlockFrame }) {
  return (
    <pre className={styles.codeBlock} data-language={frame.language || undefined}>
      {frame.source}
    </pre>
  );
}

export function describeCodeBlock(frame: CodeBlockFrame): string {
  return frame.caption || (frame.language ? `${frame.language} code` : "Code block");
}

function registerDefaults() {
  if (getTeachRenderer("growth_table")) return;

  registerTeachRender({
    types: ["growth_table"],
    describe: (f) => describeGrowthTable(f as GrowthTableFrame),
    render: (f) => <GrowthTable frame={f as GrowthTableFrame} scoped />,
  });
  registerTeachRender({
    types: ["growth_workers"],
    describe: (f) => describeGrowthWorkers(f as GrowthWorkersFrame),
    render: (f) => (
      <div className={styles.workers}>
        <GrowthWorkers frame={f as GrowthWorkersFrame} />
      </div>
    ),
  });
  registerTeachRender({
    types: ["growth_curve"],
    describe: (f) => describeGrowthCurve(f as GrowthCurveFrame),
    render: (f) => (
      <div className={styles.curve}>
        <GrowthCurve frame={f as GrowthCurveFrame} />
      </div>
    ),
  });
  registerTeachRender({
    types: ["mermaid", "mermaid_flow"],
    describe: (f) => (f as MermaidFlowFrame).caption || "Mermaid diagram",
    render: (f) => {
      const mf = f as MermaidFlowFrame;
      return (
        <MermaidDiagram
          source={mf.source}
          revealedNodes={mf.revealed_nodes}
          direction={mf.direction}
          zoomPan={mf.zoom_pan}
          caption={mf.caption}
        />
      );
    },
  });
  registerTeachRender({
    types: ["code_block"],
    describe: (f) => describeCodeBlock(f as CodeBlockFrame),
    render: (f) => <CodeBlockView frame={f as CodeBlockFrame} />,
  });
  registerTeachRender({
    types: ["fraction_bar"],
    describe: (f) => describeFractionBar(f as FractionBarFrame),
    render: (f) => {
      const fb = f as FractionBarFrame;
      return (
        <>
          <FractionBar frame={fb} />
          {fb.number_line && (
            <NumberLine max={fb.number_line.max} ticks={fb.number_line.ticks} marks={fb.number_line.marks} />
          )}
        </>
      );
    },
  });
  registerTeachRender({
    types: ["box_index"],
    describe: (f) => describeBoxIndex(f as BoxIndexFrame),
    render: (f) => <BoxIndex frame={f as BoxIndexFrame} />,
  });
  registerTeachRender({
    types: ["code_tree"],
    describe: (f) => describeCodeTree(f as CodeTreeFrame),
    render: (f) => <CodeTree frame={f as CodeTreeFrame} />,
  });
  registerTeachRender({
    types: ["sticks_boxes_complexity", "interactive_ops_boxes"],
    describe: (f) => describeSticksBoxesComplexity(f as SticksBoxesComplexityFrame),
    render: (f) => <SticksBoxesComplexity frame={f as SticksBoxesComplexityFrame} />,
  });
}

registerDefaults();

/** Frame → typed render inside the isolated island. */
export default function TeachRenderBox({ frame }: { frame: FrameType | null | undefined }) {
  // Explain-again rotate can briefly hand the stepper an undefined slot
  // (stale index or a hole in teach_frames). Never read `.type` on that.
  if (!frame || typeof frame.type !== "string") return null;
  const kind = canonicalTeachRenderType(frame.type);
  const entry = getTeachRenderer(kind) || getTeachRenderer(frame.type);
  if (!entry) return null;
  const caption = "caption" in frame ? frame.caption : undefined;
  const className =
    kind === "growth_table"
      ? styles.scoreboard
      : kind === "growth_workers"
        ? styles.workers
        : kind === "growth_curve"
          ? styles.curve
          : kind === "sticks_boxes_complexity"
            ? styles.sticksBoxes
            : undefined;
  return (
    <PresentationIsland kind={kind} label={entry.describe(frame)} caption={caption} className={className}>
      {entry.render(frame)}
    </PresentationIsland>
  );
}

export { styles as teachRenderStyles };
