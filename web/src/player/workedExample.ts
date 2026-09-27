import type { Frame, WorkedExample } from "../api";

export type WorkedExampleParts = { md: string | null; steps: string[]; frames: Frame[] };

/**
 * Normalise a worked-example card payload into renderable parts.
 *
 * The card arrives either as a single `md` block, as a list of `steps_md`, or as
 * a stripped payload that carries neither. Every field is optional here so a
 * partial payload renders an empty state instead of throwing during render.
 */
export function workedExampleParts(example: WorkedExample | null | undefined): WorkedExampleParts {
  if (!example) return { md: null, steps: [], frames: [] };
  const raw = example as { md?: unknown; steps_md?: unknown; frames?: unknown };
  const md = typeof raw.md === "string" && raw.md.trim().length > 0 ? raw.md : null;
  const steps = Array.isArray(raw.steps_md)
    ? raw.steps_md.filter((step): step is string => typeof step === "string" && step.trim().length > 0)
    : [];
  const frames = Array.isArray(raw.frames)
    ? raw.frames.filter((frame): frame is Frame => !!frame && typeof (frame as { type?: unknown }).type === "string")
    : [];
  return { md, steps, frames };
}