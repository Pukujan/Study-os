import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { render } from "../test-utils";
import CompanionPanel from "./CompanionPanel";
import type { PlayerView } from "../api";

// jsdom gaps used by the panel and its Sprite: scrollIntoView + matchMedia.
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn();
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia;
});

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

function view(): PlayerView {
  return {
    session_id: "s1",
    lesson: {
      lesson_id: "fractions-compare",
      revision: "r1",
      title: "Comparing fractions",
      lane: "hesi",
      representation: "fraction_bar",
      total_steps: 3,
    },
    step: {
      step_id: "step-1",
      concept_id: "fractions.compare",
      index: 0,
      teach_md: "Two bars, same whole.",
      teach_frames: [],
      teach_collapsed: false,
      probe: null,
      variant: 0,
    },
    phase: "probe",
    presentation_version: 1,
    presentation_update: null,
    feedback: null,
    scaffold: 0,
    progress: { done: 0, total: 3 },
    is_guest: true,
  };
}

function mount() {
  return render(
    <CompanionPanel
      sessionId="s1"
      stepId="step-1"
      view={view()}
      open
      onClose={() => {}}
      onViewChange={() => {}}
    />,
  );
}

async function sendMessage(container: HTMLElement) {
  const input = container.querySelector<HTMLInputElement>('input[aria-label="Message"]');
  const form = container.querySelector<HTMLFormElement>("form.companion-input");
  await act(async () => {
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
      setter?.call(input, "What should I notice?");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
  await act(async () => {
    form?.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
}

describe("CompanionPanel chat ack (#126 A13)", () => {
  // Product truth (PDD_UX_DEFECT_EXPLORATION section 2): "Study-buddy chat ack --
  // Sending a chat message shows an ack (pending/sent/error) or assistant reply
  // region update within 3s; no silent drop."
  //
  // The tutor call can take >20s (measured 9s-23s live), so the pending ack must
  // be observable on its own, without waiting for the reply.
  it("shows an observable pending ack immediately, before the tutor replies", async () => {
    // Tutor request stays pending: no reply will ever land in this test.
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));

    const { container, cleanup } = mount();
    await sendMessage(container);

    const text = container.textContent ?? "";
    expect(
      text,
      "an observable ack must appear before the tutor reply resolves (no silent drop)",
    ).toMatch(/thinking|got it|working|one moment|on it/i);
    cleanup();
  });

  it("keeps the thinking indicator labeled for assistive tech", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));
    const { container, cleanup } = mount();
    await sendMessage(container);

    const thinking = container.querySelector(".thinking-bubble");
    expect(thinking).not.toBeNull();
    const label = thinking?.getAttribute("aria-label") ?? thinking?.textContent ?? "";
    expect(label.trim().length, "thinking bubble needs a non-empty accessible label").toBeGreaterThan(0);
    cleanup();
  });
});
