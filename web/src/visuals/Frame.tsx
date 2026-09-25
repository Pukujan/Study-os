import type { Frame as FrameType } from "../api";
import FractionBar, { describeFractionBar } from "./FractionBar";
import NumberLine from "./NumberLine";
import BoxIndex, { describeBoxIndex } from "./BoxIndex";
import MermaidDiagram from "./MermaidDiagram";
import CodeTree, { describeCodeTree } from "./CodeTree";

export function describeFrame(frame: FrameType): string {
  if (frame.type === "fraction_bar") return describeFractionBar(frame);
  if (frame.type === "box_index") return describeBoxIndex(frame);
  if (frame.type === "mermaid_flow") return frame.caption || "Mermaid diagram";
  if (frame.type === "code_tree") return describeCodeTree(frame);
  return "Frame";
}

export default function Frame({ frame }: { frame: FrameType }) {
  if (frame.type === "fraction_bar") {
    const fb = frame;
    return (
      <figure className="frame-figure">
        <FractionBar frame={fb} />
        {fb.number_line && <NumberLine max={fb.number_line.max} ticks={fb.number_line.ticks} marks={fb.number_line.marks} />}
        {fb.caption && <figcaption className="frame-caption">{fb.caption}</figcaption>}
      </figure>
    );
  }
  if (frame.type === "box_index") {
    const bi = frame;
    return (
      <figure className="frame-figure">
        <BoxIndex frame={bi} />
        {bi.caption && <figcaption className="frame-caption">{bi.caption}</figcaption>}
      </figure>
    );
  }
  if (frame.type === "mermaid_flow") {
    const mf = frame;
    return (
      <figure className="frame-figure">
        <MermaidDiagram
          source={mf.source}
          revealedNodes={mf.revealed_nodes}
          direction={mf.direction}
          zoomPan={mf.zoom_pan}
          caption={mf.caption}
        />
        {mf.caption && <figcaption className="frame-caption">{mf.caption}</figcaption>}
      </figure>
    );
  }
  if (frame.type === "code_tree") {
    const ct = frame;
    return (
      <figure className="frame-figure">
        <CodeTree frame={ct} />
        {ct.caption && <figcaption className="frame-caption">{ct.caption}</figcaption>}
      </figure>
    );
  }
  return null;
}
