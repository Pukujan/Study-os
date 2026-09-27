/**
 * Isolated teach-render island (PresentationIsland / TeachRenderBox).
 *
 * Scoped CSS modules own layout so global page flex cannot stretch scoreboards.
 * growth_* frames mount here; ascii/code/mermaid/fraction/box also typed slots.
 */
import type { CSSProperties, ReactNode } from "react";
import type { Frame as FrameType } from "../api";
import FractionBar, { describeFractionBar } from "./FractionBar";
import NumberLine from "./NumberLine";
import BoxIndex, { describeBoxIndex } from "./BoxIndex";
import MermaidDiagram from "./MermaidDiagram";
import CodeTree, { describeCodeTree } from "./CodeTree";
import GrowthTable, { describeGrowthTable } from "./GrowthTable";
import GrowthWorkers, { describeGrowthWorkers } from "./GrowthWorkers";
import GrowthCurve, { describeGrowthCurve } from "./GrowthCurve";
import styles from "./TeachRenderBox.module.css";

export type TeachRenderKind =
  | "growth_table"
  | "growth_workers"
  | "growth_curve"
  | "fraction_bar"
  | "box_index"
  | "mermaid_flow"
  | "code_tree"
  | "ascii"
  | "code"
  | "svg";

type IslandProps = {
  kind: TeachRenderKind | string;
  label?: string;
  children: ReactNode;
  caption?: string | null;
  className?: string;
  style?: CSSProperties;
};

/** Shadow-like scoped shell for any teach visual. */
export function PresentationIsland({ kind, label, children, caption, className, style }: IslandProps) {
  const cls = [styles.island, className].filter(Boolean).join(" ");
  return (
    <figure
      className={cls}
      data-teach-render={kind}
      data-testid="teach-render-box"
      aria-label={label || undefined}
      style={style}
    >
      {children}
      {caption ? <figcaption className={styles.caption}>{caption}</figcaption> : null}
    </figure>
  );
}

/** Frame → typed render inside the isolated island. */
export default function TeachRenderBox({ frame }: { frame: FrameType }) {
  if (frame.type === "growth_table") {
    return (
      <PresentationIsland
        kind="growth_table"
        label={describeGrowthTable(frame)}
        caption={frame.caption}
        className={styles.scoreboard}
      >
        <GrowthTable frame={frame} scoped />
      </PresentationIsland>
    );
  }
  if (frame.type === "growth_workers") {
    return (
      <PresentationIsland
        kind="growth_workers"
        label={describeGrowthWorkers(frame)}
        caption={frame.caption}
        className={styles.workers}
      >
        <GrowthWorkers frame={frame} />
      </PresentationIsland>
    );
  }
  if (frame.type === "growth_curve") {
    return (
      <PresentationIsland
        kind="growth_curve"
        label={describeGrowthCurve(frame)}
        caption={frame.caption}
        className={styles.curve}
      >
        <GrowthCurve frame={frame} />
      </PresentationIsland>
    );
  }
  if (frame.type === "fraction_bar") {
    return (
      <PresentationIsland kind="fraction_bar" label={describeFractionBar(frame)} caption={frame.caption}>
        <FractionBar frame={frame} />
        {frame.number_line && (
          <NumberLine max={frame.number_line.max} ticks={frame.number_line.ticks} marks={frame.number_line.marks} />
        )}
      </PresentationIsland>
    );
  }
  if (frame.type === "box_index") {
    return (
      <PresentationIsland kind="box_index" label={describeBoxIndex(frame)} caption={frame.caption}>
        <BoxIndex frame={frame} />
      </PresentationIsland>
    );
  }
  if (frame.type === "mermaid_flow") {
    return (
      <PresentationIsland kind="mermaid_flow" label={frame.caption || "Mermaid diagram"} caption={frame.caption}>
        <MermaidDiagram
          source={frame.source}
          revealedNodes={frame.revealed_nodes}
          direction={frame.direction}
          zoomPan={frame.zoom_pan}
          caption={frame.caption}
        />
      </PresentationIsland>
    );
  }
  if (frame.type === "code_tree") {
    return (
      <PresentationIsland kind="code_tree" label={describeCodeTree(frame)} caption={frame.caption}>
        <CodeTree frame={frame} />
      </PresentationIsland>
    );
  }
  return null;
}

export function AsciiRender({ text, caption }: { text: string; caption?: string }) {
  return (
    <PresentationIsland kind="ascii" label={caption || "ASCII diagram"} caption={caption}>
      <pre className={styles.ascii}>{text}</pre>
    </PresentationIsland>
  );
}

export function CodeRender({ text, caption }: { text: string; caption?: string }) {
  return (
    <PresentationIsland kind="code" label={caption || "Code"} caption={caption}>
      <pre className={styles.code}>{text}</pre>
    </PresentationIsland>
  );
}

export { styles as teachRenderStyles };
