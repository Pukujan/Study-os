import { afterEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { createRoot } from "react-dom/client";
import type { ReactElement } from "react";
import { render } from "../test-utils";
import FeedbackBar from "./FeedbackBar";

function draftStep(container: HTMLElement, score: number, why: string) {
  const rating = container.querySelector<HTMLButtonElement>(`button[aria-label='Rate ${score} out of 5']`);
  act(() => rating?.click());
  const textarea = container.querySelector<HTMLTextAreaElement>("textarea[aria-label='Why this rating?']");
  act(() => {
    const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
    setValue?.call(textarea, why);
    textarea?.dispatchEvent(new Event("input", { bubbles: true }));
  });
  return { rating, textarea };
}

// A real re-render of the same mounted tree, so draft/identity behavior is
// exercised the way a chat re-render or step change reaches the component.
function mount(ui: ReactElement) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(ui));
  return {
    container,
    rerender: (next: ReactElement) => act(() => root.render(next)),
    cleanup: () => {
      act(() => root.unmount());
      document.body.removeChild(container);
    },
  };
}

afterEach(() => vi.unstubAllGlobals());

describe("learner step review contract (#126)", () => {
  it("keeps 1-5 and typed why as a draft until explicit Submit", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true, feedback_id: "f1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const { container, cleanup } = render(
      <FeedbackBar session_id="s1" step_id="position" target_kind="step" target_id="position:-1" {...{ presentation_version: 1 }} />,
    );
    try {
      const submit = container.querySelector<HTMLButtonElement>("button[type='submit']");
      expect(submit?.textContent).toMatch(/Submit/i);
      expect(submit?.disabled).toBe(true);
      const score = container.querySelector<HTMLButtonElement>("button[aria-label='Rate 4 out of 5']");
      expect(score).not.toBeNull();
      act(() => score?.click());
      expect(fetchMock).not.toHaveBeenCalled();
      expect(submit?.disabled).toBe(true);

      const why = container.querySelector<HTMLTextAreaElement>("textarea[aria-label='Why this rating?']");
      expect(why).not.toBeNull();
      act(() => {
        const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
        setValue?.call(why, "The box helped; the index label was unclear.");
        why?.dispatchEvent(new Event("input", { bubbles: true }));
      });
      expect(fetchMock).not.toHaveBeenCalled();
      expect(submit?.disabled).toBe(false);
      await act(async () => submit?.click());
      expect(fetchMock).toHaveBeenCalledTimes(1);
      const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
      expect(body.rating).toBe(4);
      expect(body.free_text).toBe("The box helped; the index label was unclear.");
      expect(body.step_id).toBe("position");
      expect(body.target_id).toBe("position:-1");
      expect(body.presentation_version).toBe(1);
      expect(body.idempotency_key).toMatch(/^[0-9a-f-]{36}$/i);
    } finally {
      cleanup();
    }
  });

  it("keeps the draft and key across a same-step re-render, clearing on step change", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true, feedback_id: "f2" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const step = (version: number, stepId = "position", variant = -1) => (
      <FeedbackBar
        session_id="s1"
        step_id={stepId}
        target_kind="step"
        target_id={`${stepId}:${variant}`}
        presentation_version={version}
      />
    );
    const { container, rerender, cleanup } = mount(step(1));
    try {
      draftStep(container, 4, "The box helped.");
      expect(fetchMock).not.toHaveBeenCalled();

      // A chat re-render of the same step keeps the draft and its idempotency key.
      await rerender(step(2));
      const submit = container.querySelector<HTMLButtonElement>("button[type='submit']");
      expect(submit?.disabled).toBe(false);
      await act(async () => submit?.click());
      expect(fetchMock).toHaveBeenCalledTimes(1);
      const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
      expect(body.rating).toBe(4);
      expect(body.free_text).toBe("The box helped.");
      expect(body.presentation_version).toBe(2);
      expect(body.idempotency_key).toMatch(/^[0-9a-f-]{36}$/i);
    } finally {
      cleanup();
    }
  });

  it("discards the draft when the step or variant changes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true, feedback_id: "f3" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const { container, rerender, cleanup } = mount(
      <FeedbackBar session_id="s1" step_id="position" target_kind="step" target_id="position:-1" {...{ presentation_version: 1 }} />,
    );
    try {
      draftStep(container, 5, "A review of the first step.");
      const submit = container.querySelector<HTMLButtonElement>("button[type='submit']");
      expect(submit?.disabled).toBe(false);

      // A different step must not inherit a stale draft.
      await rerender(
        <FeedbackBar session_id="s1" step_id="index" target_kind="step" target_id="index:-1" {...{ presentation_version: 1 }} />,
      );
      const moved = container.querySelector<HTMLButtonElement>("button[type='submit']");
      expect(moved?.disabled).toBe(true);
      const cleared = container.querySelector<HTMLTextAreaElement>("textarea[aria-label='Why this rating?']");
      expect(cleared?.value).toBe("");
      expect(container.querySelector<HTMLButtonElement>("button[aria-label='Rate 5 out of 5']")?.getAttribute("aria-pressed")).toBe("false");
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      cleanup();
    }
  });
});
