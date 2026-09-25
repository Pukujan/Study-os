import { useState } from "react";
import type { Frame as FrameType } from "../api";
import Frame from "./Frame";

export default function FrameStepper({ frames, label }: { frames: FrameType[]; label?: string }) {
  const [index, setIndex] = useState(0);
  const total = frames.length;
  if (total === 0) return null;

  const showControls = total > 1;
  const current = frames[index];

  return (
    <div className="frame-stepper" aria-label={label || "Step through frames"}>
      <Frame frame={current} />
      {showControls && (
        <div className="frame-stepper-controls">
          <button
            className="btn small"
            onClick={() => setIndex((i) => Math.max(0, i - 1))}
            disabled={index === 0}
            aria-label="Previous frame"
            data-track="framestepper.back"
          >
            Back
          </button>
          <span className="frame-stepper-count" aria-live="polite">
            {index + 1} of {total}
          </span>
          <button
            className="btn small"
            onClick={() => setIndex((i) => Math.min(total - 1, i + 1))}
            disabled={index === total - 1}
            aria-label="Next frame"
            data-track="framestepper.next"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
