import type { Frame as FrameType } from "../api";
import TeachRenderBox from "./TeachRenderBox";
import { describeFractionBar } from "./FractionBar";
import { describeBoxIndex } from "./BoxIndex";
import { describeCodeTree } from "./CodeTree";
import { describeGrowthTable } from "./GrowthTable";
import { describeGrowthWorkers } from "./GrowthWorkers";
import { describeGrowthCurve } from "./GrowthCurve";
import { describeInteractiveVisual } from "./InteractiveVisual";
import { describeCuratedDiagram } from "./CuratedDiagram";

export function describeFrame(frame: FrameType): string {
  if (frame.type === "fraction_bar") return describeFractionBar(frame);
  if (frame.type === "box_index") return describeBoxIndex(frame);
  if (frame.type === "mermaid_flow") return frame.caption || "Mermaid diagram";
  if (frame.type === "code_tree") return describeCodeTree(frame);
  if (frame.type === "growth_table") return describeGrowthTable(frame);
  if (frame.type === "growth_workers") return describeGrowthWorkers(frame);
  if (frame.type === "growth_curve") return describeGrowthCurve(frame);
  if (frame.type === "interactive_visual") return describeInteractiveVisual(frame);
  if (frame.type === "curated_diagram") return describeCuratedDiagram(frame);
  return "Frame";
}

/** All teach frames mount through the isolated TeachRenderBox island. */
export default function Frame({ frame }: { frame: FrameType }) {
  return <TeachRenderBox frame={frame} />;
}
