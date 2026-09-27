import type { Frame as FrameType } from "../api";
import TeachRenderBox from "./TeachRenderBox";
import { describeFractionBar } from "./FractionBar";
import { describeBoxIndex } from "./BoxIndex";
import { describeCodeTree } from "./CodeTree";
import { describeGrowthTable } from "./GrowthTable";
import { describeGrowthWorkers } from "./GrowthWorkers";
import { describeGrowthCurve } from "./GrowthCurve";
import { isRenderableFrame } from "./frames";

export function describeFrame(frame: FrameType | null | undefined): string {
  if (!isRenderableFrame(frame)) return "Frame";
  if (frame.type === "fraction_bar") return describeFractionBar(frame);
  if (frame.type === "box_index") return describeBoxIndex(frame);
  if (frame.type === "mermaid_flow") return frame.caption || "Mermaid diagram";
  if (frame.type === "code_tree") return describeCodeTree(frame);
  if (frame.type === "growth_table") return describeGrowthTable(frame);
  if (frame.type === "growth_workers") return describeGrowthWorkers(frame);
  if (frame.type === "growth_curve") return describeGrowthCurve(frame);
  return "Frame";
}

/** All teach frames mount through the isolated TeachRenderBox island. */
export default function Frame({ frame }: { frame: FrameType | null | undefined }) {
  if (!isRenderableFrame(frame)) return null;
  return <TeachRenderBox frame={frame} />;
}
