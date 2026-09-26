import { afterEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import FeedbackBar from "./FeedbackBar";

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
});
