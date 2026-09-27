import { describe, expect, it } from "vitest";
import type { PlayerView, PresentationUpdate } from "../api";
import { applyPresentation } from "./presentation";

function view(overrides: Partial<PlayerView> = {}): PlayerView {
  return {
    session_id: "s1",
    lesson: { lesson_id: "l", revision: "l.v1", title: "T", lane: "dsa", representation: "box_index", total_steps: 3 },
    step: {
      step_id: "position",
      concept_id: "sliding-window.position",
      index: 1,
      teach_md: "authored",
      teach_frames: [],
      teach_collapsed: false,
      probe: { prompt_md: "Which position?", frames: [], answer_kind: "integer", choices: [] },
      variant: -1,
    },
    phase: "probe",
    presentation_version: 0,
    presentation_update: null,
    feedback: null,
    scaffold: 0,
    progress: { done: 1, total: 3 },
    card_mode: "probe",
    variant_tag: null,
    can_go_back: false,
    worked_example: undefined,
    is_guest: false,
    ...overrides,
  };
}

function update(overrides: Partial<PresentationUpdate> = {}): PresentationUpdate {
  return {
    schema_version: "study-os.player-presentation.v1",
    operation: "regenerate_presentation",
    lesson_id: "l",
    lesson_revision: "l.v1",
    step_id: "position",
    concept_id: "sliding-window.position",
    variant: -1,
    phase: "probe",
    card_mode: "probe",
    scaffold: 0,
    previous_version: 0,
    version: 1,
    teach_md: "regenerated",
    teach_frames: [{ type: "box_index", array: [4, 7, 2], show_positions: true, show_indices: false }],
    provenance: { prompt_version: "tutor.v3", model: "stub", route: "stub", served: "generated" },
    ...overrides,
  };
}

describe("applyPresentation", () => {
  it("replaces the displayed teach content without moving the step", () => {
    const before = view();
    const after = applyPresentation(before, update());

    expect(after).not.toBe(before);
    expect(after.step.teach_md).toBe("regenerated");
    expect(after.step.teach_frames).toHaveLength(1);
    expect(after.presentation_version).toBe(1);
    expect(after.presentation_update?.version).toBe(1);

    // Identity, phase, variant and progress are untouched.
    expect(after.step.step_id).toBe(before.step.step_id);
    expect(after.step.concept_id).toBe(before.step.concept_id);
    expect(after.step.index).toBe(before.step.index);
    expect(after.step.variant).toBe(before.step.variant);
    expect(after.step.probe).toEqual(before.step.probe);
    expect(after.phase).toBe(before.phase);
    expect(after.progress).toEqual(before.progress);
  });

  it("ignores a null update", () => {
    const before = view();
    expect(applyPresentation(before, null)).toBe(before);
    expect(applyPresentation(before, undefined)).toBe(before);
  });

  it("ignores an update for another step or concept", () => {
    const before = view();
    expect(applyPresentation(before, update({ step_id: "index" }))).toBe(before);
    expect(applyPresentation(before, update({ concept_id: "sliding-window.index" }))).toBe(before);
  });

  it("ignores a stale or replayed version", () => {
    const before = view({ presentation_version: 2, presentation_update: update({ version: 2, previous_version: 1 }) });
    expect(applyPresentation(before, update({ version: 2, previous_version: 1 }))).toBe(before);
    expect(applyPresentation(before, update({ version: 1, previous_version: 0 }))).toBe(before);
  });
});


