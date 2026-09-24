import type { Frame as FrameType, FractionBarFrame, BoxIndexFrame } from "../api";
import FractionBar, { describeFractionBar } from "./FractionBar";
import NumberLine from "./NumberLine";
import BoxIndex, { describeBoxIndex } from "./BoxIndex";

export function describeFrame(frame: FrameType): string {
  if (frame.type === "fraction_bar") return describeFractionBar(frame);
  return describeBoxIndex(frame);
}

export default function Frame({ frame }: { frame: FrameType }) {
  if (frame.type === "fraction_bar") {
    const fb = frame as FractionBarFrame;
    return (
      <figure className="frame-figure">
        <FractionBar frame={fb} />
        {fb.number_line && <NumberLine max={fb.number_line.max} ticks={fb.number_line.ticks} marks={fb.number_line.marks} />}
        {fb.caption && <figcaption className="frame-caption">{fb.caption}</figcaption>}
      </figure>
    );
  }
  const bi = frame as BoxIndexFrame;
  return (
    <figure className="frame-figure">
      <BoxIndex frame={bi} />
      {bi.caption && <figcaption className="frame-caption">{bi.caption}</figcaption>}
    </figure>
  );
}
