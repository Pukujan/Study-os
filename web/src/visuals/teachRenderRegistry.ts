/**
 * Teach-render type registry.
 *
 * New island render types register here (or via `registerTeachRender`) so
 * Frame / TeachRenderBox stay a thin dispatcher. Aliases (e.g. mermaid →
 * mermaid_flow) share one renderer.
 */
import type { ReactNode } from "react";
import type { Frame as FrameType } from "../api";

export type TeachRenderType =
  | "code_block"
  | "mermaid"
  | "mermaid_flow"
  | "growth_workers"
  | "growth_curve"
  | "growth_table"
  | "fraction_bar"
  | "box_index"
  | "code_tree"
  | "sticks_boxes_complexity"
  | "interactive_ops_boxes";

export type TeachRenderer = {
  /** Canonical kind + aliases that share this renderer. */
  types: readonly TeachRenderType[];
  describe: (frame: FrameType) => string;
  render: (frame: FrameType) => ReactNode;
};

const byType = new Map<string, TeachRenderer>();

/** Register (or replace) a teach-render type. Call at module load for builtins. */
export function registerTeachRender(renderer: TeachRenderer): void {
  for (const t of renderer.types) {
    byType.set(t, renderer);
  }
}

export function getTeachRenderer(type: string): TeachRenderer | undefined {
  return byType.get(type);
}

export function listTeachRenderTypes(): string[] {
  return [...byType.keys()].sort();
}

/** Normalize authored aliases before lookup. */
export function canonicalTeachRenderType(type: string): string {
  if (type === "mermaid") return "mermaid_flow";
  if (type === "interactive_ops_boxes") return "sticks_boxes_complexity";
  return type;
}
