import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import type { PlayerView } from "../api";
import { render } from "../test-utils";

const baseView: PlayerView = {
  session_id: "sess-1",
  lesson: {
    lesson_id: "demo",
    revision: "1",
    title: "Demo",
    lane: "dsa",
    representation: "box_index",
    total_steps: 2,
  },
  step: {
    step_id: "s1",
    concept_id: "c1",
    index: 0,
    teach_md: "Teach text.",
    teach_frames: [],
    teach_collapsed: false,
    probe: {
      prompt_md: "What is 1+1?",
      frames: [],
      answer_kind: "text",
      choices: [],
    },
    variant: -1,
  },
  phase: "probe",
  presentation_version: 0,
  presentation_update: null,
  feedback: null,
  scaffold: 0,
  progress: { done: 0, total: 2 },
  card_mode: "probe",
  variant_tag: null,
  can_go_back: false,
  can_revisit_step: false,
  worked_example: undefined,
  is_guest: false,
};

async function flush() {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 40));
  });
}

function route(url: string): string {
  const u = String(url);
  if (u.endsWith("/adapt")) return "adapt";
  if (u.endsWith("/tutor")) return "tutor";
  if (u.endsWith("/confused")) return "confused";
  if (/\/api\/player\/sessions\/[^/]+$/.test(u)) return "get";
  return "other";
}

describe("Player teach-panel regen chips", () => {
  beforeEach(() => {
    localStorage.setItem("sos.pet.hidden", "true");
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    localStorage.removeItem("sos.pet.hidden");
  });

  it("Worked example calls adapt(example) and shows the card", async () => {
    const adapt = vi.fn();
    const tutor = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        switch (route(url)) {
          case "get":
            return new Response(JSON.stringify(baseView), { status: 200 });
          case "adapt": {
            const body = JSON.parse(String(init?.body || "{}"));
            expect(body.kind).toBe("example");
            adapt();
            return new Response(
              JSON.stringify({
                ...baseView,
                card_mode: "worked_example",
                variant_tag: "example",
                worked_example: { md: "1 + 1 = 2", frames: [] },
                step: { ...baseView.step, probe: null },
                can_go_back: true,
              }),
              { status: 200 },
            );
          }
          case "tutor":
            tutor();
            return new Response(JSON.stringify({ reply_md: "ok" }), { status: 200 });
          default:
            return new Response(JSON.stringify({ ok: true }), { status: 200 });
        }
      }),
    );

    const { default: Player } = await import("./Player");
    const { container, cleanup } = render(<Player sessionId="sess-1" />);
    await flush();
    await flush();

    const btn = container.querySelector('[data-testid="player.step.regen-example"]') as HTMLButtonElement | null;
    expect(btn).toBeTruthy();
    await act(async () => {
      btn!.click();
    });
    await flush();
    await flush();

    expect(adapt).toHaveBeenCalled();
    expect(tutor).not.toHaveBeenCalled();
    expect(container.textContent).toContain("1 + 1 = 2");
    expect(container.querySelector("[data-testid='worked-example']")).toBeTruthy();
    cleanup();
  }, 15000);

  it("Worked example re-click applies alternate card content", async () => {
    let adaptCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        switch (route(url)) {
          case "get":
            return new Response(
              JSON.stringify({
                ...baseView,
                card_mode: "worked_example",
                variant_tag: "example",
                worked_example: { md: "1 + 1 = 2", frames: [] },
                step: { ...baseView.step, probe: null },
                can_go_back: true,
              }),
              { status: 200 },
            );
          case "adapt": {
            const body = JSON.parse(String(init?.body || "{}"));
            expect(body.kind).toBe("example");
            adaptCalls += 1;
            return new Response(
              JSON.stringify({
                ...baseView,
                card_mode: "worked_example",
                variant_tag: "example_alt",
                worked_example: { md: "Another look: 1 + 1 = 2", frames: [] },
                step: { ...baseView.step, probe: null },
                can_go_back: true,
              }),
              { status: 200 },
            );
          }
          default:
            return new Response(JSON.stringify({ ok: true }), { status: 200 });
        }
      }),
    );

    const { default: Player } = await import("./Player");
    const { container, cleanup } = render(<Player sessionId="sess-1" />);
    await flush();
    await flush();

    expect(container.textContent).toContain("1 + 1 = 2");
    const btn = container.querySelector('[data-testid="player.step.regen-example"]') as HTMLButtonElement | null;
    expect(btn).toBeTruthy();
    await act(async () => {
      btn!.click();
    });
    await flush();
    await flush();

    expect(adaptCalls).toBe(1);
    expect(container.textContent).toContain("Another look: 1 + 1 = 2");
    cleanup();
  }, 15000);

  it("Explain again falls back to confused when tutor returns no presentation", async () => {
    const tutor = vi.fn();
    const confused = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        switch (route(url)) {
          case "get":
            return new Response(JSON.stringify(baseView), { status: 200 });
          case "tutor":
            tutor();
            return new Response(JSON.stringify({ reply_md: "text only", regenerate_presentation: null }), {
              status: 200,
            });
          case "confused":
            confused();
            return new Response(
              JSON.stringify({
                ...baseView,
                phase: "feedback",
                feedback: {
                  outcome: "incorrect",
                  message_md: "Let's look at this again.",
                  frames: [],
                  next_action: "retry_same",
                  sticker: "reassure",
                  reassure: true,
                },
              }),
              { status: 200 },
            );
          default:
            return new Response(JSON.stringify({ ok: true }), { status: 200 });
        }
      }),
    );

    const { default: Player } = await import("./Player");
    const { container, cleanup } = render(<Player sessionId="sess-1" />);
    await flush();
    await flush();

    const btn = container.querySelector('[data-testid="player.step.regen-reexplain"]') as HTMLButtonElement | null;
    expect(btn).toBeTruthy();
    await act(async () => {
      btn!.click();
    });
    await flush();
    await flush();

    expect(tutor).toHaveBeenCalled();
    expect(confused).toHaveBeenCalled();
    expect(container.textContent).toContain("Let's look at this again.");
    cleanup();
  }, 15000);
});
