import { afterEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import FeedbackBar from "./FeedbackBar";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("FeedbackBar", () => {
  it("sends the right body on dislike with reasons", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true, feedback_id: "f1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const { container, cleanup } = render(
      <FeedbackBar
        session_id="s1"
        step_id="step-a"
        target_kind="step"
        target_id="step-a:1"
      />,
    );

    const dislike = container.querySelector<HTMLButtonElement>("button[aria-label='Not helpful']");
    act(() => dislike?.click());

    const chip = container.querySelector<HTMLButtonElement>("button[data-track='feedback.reason.confusing']");
    act(() => chip?.click());

    const send = container.querySelector<HTMLButtonElement>("button[data-track='feedback.send']");
    await act(async () => send?.click());

    const calls = fetchMock.mock.calls;
    expect(calls.length).toBeGreaterThan(0);
    const init = calls[calls.length - 1][1] as RequestInit;
    const body = JSON.parse(init.body as string);
    expect(body).toEqual({
      session_id: "s1",
      step_id: "step-a",
      target_kind: "step",
      target_id: "step-a:1",
      rating: "dislike",
      reasons: ["confusing"],
    });
    cleanup();
  });
});
