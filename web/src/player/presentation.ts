import type { PlayerView, PresentationUpdate } from "../api";

/**
 * Apply a chat-triggered re-render to the current step in place.
 *
 * The step, variant, phase and progress are untouched: only the displayed teach
 * content changes. Updates for another step/concept, or ones that are not newer
 * than what is already shown, are ignored.
 */
export function applyPresentation(view: PlayerView, update: PresentationUpdate | null | undefined): PlayerView {
  if (!update) return view;
  if (update.step_id !== view.step.step_id || update.concept_id !== view.step.concept_id) return view;
  if (update.version <= view.presentation_version) return view;
  return {
    ...view,
    step: { ...view.step, teach_md: update.teach_md, teach_frames: update.teach_frames },
    presentation_version: update.version,
    presentation_update: update,
  };
}
