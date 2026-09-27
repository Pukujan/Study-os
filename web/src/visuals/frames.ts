import type { Frame } from "../api";

/** True when a payload can safely be handed to Frame / TeachRenderBox. */
export function isRenderableFrame(frame: unknown): frame is Frame {
  return !!frame && typeof frame === "object" && typeof (frame as { type?: unknown }).type === "string";
}

/** Drop holes / malformed entries so steppers never pass `undefined` into `.type`. */
export function sanitizeFrames(frames: unknown): Frame[] {
  if (!Array.isArray(frames)) return [];
  return frames.filter(isRenderableFrame);
}
