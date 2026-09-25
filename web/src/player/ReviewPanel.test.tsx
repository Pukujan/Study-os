import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import ReviewPanel from "./ReviewPanel";

let fetchMock: Mock;

function jsonRes(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("ReviewPanel", () => {
  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  function panelProps() {
    return {
      sessionId: "sess-1",
      stepId: "step-a",
      variant: 2,
      conceptId: "frac.denominator",
    };
  }

  it("renders 1-5 rating options and optional why field", () => {
    const { container, cleanup } = render(<ReviewPanel {...panelProps()} />);
    expect(container.querySelector('[data-testid="player.review.panel"]')).toBeTruthy();
    for (const n of [1, 2, 3, 4, 5]) {
      const radio = container.querySelector<HTMLInputElement>(`[data-testid="player.review.score-${n}"]`);
      expect(radio, `score ${n}`).toBeTruthy();
      expect(radio?.disabled).toBe(false);
    }
    const why = container.querySelector<HTMLTextAreaElement>('[data-testid="player.review.why"]');
    expect(why).toBeTruthy();
    expect(why?.required).toBe(false);
    cleanup();
  });

  it("Submit is explicit and disabled until a rating is chosen", async () => {
    const { container, cleanup } = render(<ReviewPanel {...panelProps()} />);
    const submit = container.querySelector<HTMLButtonElement>('[data-testid="player.review.submit"]');
    expect(submit?.disabled).toBe(true);

    const three = container.querySelector<HTMLInputElement>('[data-testid="player.review.score-3"]');
    await act(async () => {
      three?.click();
    });
    const submitAfter = container.querySelector<HTMLButtonElement>('[data-testid="player.review.submit"]');
    expect(submitAfter?.disabled).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
    cleanup();
  });

  it("submits rating + why exactly once per click with a fresh idempotency key", async () => {
    const { container, cleanup } = render(<ReviewPanel {...panelProps()} />);

    const four = container.querySelector<HTMLInputElement>('[data-testid="player.review.score-4"]');
    await act(async () => {
      four?.click();
    });
    const why = container.querySelector<HTMLTextAreaElement>('[data-testid="player.review.why"]');
    await act(async () => {
      if (why) why.value = "the visual finally made it click";
      why?.dispatchEvent(new Event("input", { bubbles: true }));
    });
    const submit = container.querySelector<HTMLButtonElement>('[data-testid="player.review.submit"]');
    await act(async () => {
      submit?.click();
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/player/review");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body as string);
    expect(body).toMatchObject({
      session_id: "sess-1",
      step_id: "step-a",
      variant: 2,
      rating: 4,
      why: "the visual finally made it click",
    });
    expect(typeof body.idempotency_key).toBe("string");
    expect(body.idempotency_key.length).toBeGreaterThan(0);

    // success confirmation surface
    expect(container.querySelector('[data-testid="player.review.submitted"]')).toBeTruthy();

    // no stray duplicate POSTs from the success render
    expect(fetchMock).toHaveBeenCalledTimes(1);
    cleanup();
  });

  it("after success the form resets empty and allows another append-only rating", async () => {
    const { container, cleanup } = render(<ReviewPanel {...panelProps()} />);

    fetchMock.mockResolvedValue(jsonRes({ ok: true, review_id: "r-1" }));
    const two = container.querySelector<HTMLInputElement>('[data-testid="player.review.score-2"]');
    await act(async () => {
      two?.click();
    });
    const submit = container.querySelector<HTMLButtonElement>('[data-testid="player.review.submit"]');
    await act(async () => {
      submit?.click();
    });
    expect(container.querySelector('[data-testid="player.review.submitted"]')).toBeTruthy();

    // append-only: user can rate again; form never pre-fills the previous rating as editable
    const again = container.querySelector<HTMLInputElement>('[data-testid="player.review.score-5"]');
    expect(again, "rating still offered after submit").toBeTruthy();
    expect(again?.checked).toBe(false);
    const two2 = container.querySelector<HTMLInputElement>('[data-testid="player.review.score-2"]');
    expect(two2?.checked).toBe(false);

    const why = container.querySelector<HTMLTextAreaElement>('[data-testid="player.review.why"]');
    expect(why?.value).toBe("");
    cleanup();
  });

  it("stays usable when chat is collapsed/absent (chat never the only surface)", () => {
    const { container, cleanup } = render(
      <div className="player-layout">
        <ReviewPanel {...panelProps()} chatHidden />
      </div>,
    );
    const panel = container.querySelector('[data-testid="player.review.panel"]');
    expect(panel).toBeTruthy();
    // still interactive: radios + submit present
    expect(container.querySelector('[data-testid="player.review.score-3"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="player.review.submit"]')).toBeTruthy();
    cleanup();
  });
});
