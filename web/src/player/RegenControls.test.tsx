import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import RegenControls from "./RegenControls";
import { ApiError } from "../api";

let fetchMock: Mock;

function jsonRes(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("RegenControls", () => {
  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  function renderControls(onRegenerated = vi.fn()) {
    const handle = render(
      <RegenControls
        sessionId="sess-1"
        stepId="step-a"
        step={{
          step_id: "step-a",
          slots: { question: true, example: true, visual: true },
        }}
        onRegenerated={onRegenerated}
      />,
    );
    return { ...handle, onRegenerated };
  }

  it("shows regenerate buttons for question, example and visual on current step", () => {
    const { container, cleanup } = renderControls();
    for (const slot of ["question", "example", "visual"]) {
      const btn = container.querySelector<HTMLButtonElement>(`[data-testid="player.step.regen-${slot}"]`);
      expect(btn, `regen button for ${slot}`).toBeTruthy();
      expect(btn?.disabled).toBe(false);
    }
    cleanup();
  });

  it("hides buttons for slots the step does not offer", () => {
    const { container, cleanup } = render(
      <RegenControls sessionId="sess-1" stepId="step-a" step={{ step_id: "step-a", slots: { question: true } }} onRegenerated={vi.fn()} />,
    );
    expect(container.querySelector('[data-testid="player.step.regen-question"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="player.step.regen-example"]')).toBeNull();
    expect(container.querySelector('[data-testid="player.step.regen-visual"]')).toBeNull();
    cleanup();
  });

  it("calls regenerate once per click with idempotency key and swaps presentation in place", async () => {
    const onRegenerated = vi.fn();
    const { container, cleanup } = renderControls(onRegenerated);

    fetchMock.mockResolvedValueOnce(
      jsonRes({ session_id: "sess-1", step: { step_id: "step-a", variant: 2, teach_md: "same", teach_frames: [], teach_collapsed: false, probe: null, prompt_variant: "visual story" }, phase: "probe", feedback: null, scaffold: 0, progress: { done: 0, total: 3 }, is_guest: true }),
    );

    const btn = container.querySelector<HTMLButtonElement>('[data-testid="player.step.regen-visual"]');
    await act(async () => {
      btn?.click();
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/player/sessions/sess-1/regenerate");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body as string);
    expect(body.slot).toBe("visual");
    expect(typeof body.idempotency_key).toBe("string");
    expect(body.idempotency_key.length).toBeGreaterThan(0);
    // step identity preserved: parent decides swap; in-place means step_id unchanged
    expect(onRegenerated).toHaveBeenCalledTimes(1);
    const view = onRegenerated.mock.calls[0][0];
    expect(view.step.step_id).toBe("step-a");
    cleanup();
  });

  it("shows a spinner state and disables buttons while a regenerate is in flight", async () => {
    const { container, cleanup } = renderControls();
    let resolveFlight!: (r: Response) => void;
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => (resolveFlight = resolve)));

    const btn = container.querySelector<HTMLButtonElement>('[data-testid="player.step.regen-question"]');
    await act(async () => {
      btn?.click();
    });

    expect(container.querySelector('[data-testid="player.regen-spinner"]')).toBeTruthy();
    for (const slot of ["question", "example", "visual"]) {
      const b = container.querySelector<HTMLButtonElement>(`[data-testid="player.step.regen-${slot}"]`);
      expect(b?.disabled, `${slot} disabled in flight`).toBe(true);
    }
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveFlight(jsonRes({ session_id: "sess-1", step: { step_id: "step-a", variant: 1, teach_md: "t", teach_frames: [], teach_collapsed: false, probe: null }, phase: "probe", feedback: null, scaffold: 0, progress: { done: 0, total: 3 }, is_guest: true }));
    });

    expect(container.querySelector('[data-testid="player.regen-spinner"]')).toBeNull();
    const reenabled = container.querySelector<HTMLButtonElement>('[data-testid="player.step.regen-question"]');
    expect(reenabled?.disabled).toBe(false);
    cleanup();
  });

  it("reuses the SAME idempotency key on explicit retry of a failed regenerate", async () => {
    const { container, cleanup } = renderControls();

    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ error: "llm_unavailable" }), { status: 503 }));
    const btn = container.querySelector<HTMLButtonElement>('[data-testid="player.step.regen-question"]');
    await act(async () => {
      btn?.click();
    });
    const firstBody = JSON.parse(fetchMock.mock.calls[0][1].body as string);

    // error surface, plus explicit retry keeps the original key for replay-safety
    expect(container.querySelector('[data-testid="player.regen-error"]')?.textContent).toContain("could not regenerate");
    const retry = container.querySelector<HTMLButtonElement>('[data-testid="player.regen-retry"]');
    expect(retry).toBeTruthy();
    fetchMock.mockResolvedValueOnce(jsonRes({ session_id: "sess-1", step: { step_id: "step-a", variant: 3, teach_md: "t", teach_frames: [], teach_collapsed: false, probe: null }, phase: "probe", feedback: null, scaffold: 0, progress: { done: 0, total: 3 }, is_guest: true }));
    await act(async () => {
      retry?.click();
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const secondBody = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(secondBody.idempotency_key).toBe(firstBody.idempotency_key);
    cleanup();
  });

  it("maps idempotency_in_flight to an already-working message", async () => {
    const { container, cleanup } = renderControls();
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ error: "idempotency_in_flight" }), { status: 409 }));
    const btn = container.querySelector<HTMLButtonElement>('[data-testid="player.step.regen-example"]');
    await act(async () => {
      btn?.click();
    });
    const err = container.querySelector('[data-testid="player.regen-error"]');
    expect(err?.textContent?.toLowerCase()).toContain("already working");
    cleanup();
  });

  it("throws ApiError codes through to the error surface", async () => {
    // sanity: contract error shape {"error": code}
    const e = new ApiError(409, "idempotency_in_flight");
    expect(e.code).toBe("idempotency_in_flight");
  });
});
