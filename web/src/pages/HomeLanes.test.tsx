import { afterEach, describe, expect, it, vi } from "vitest";
import { render } from "../test-utils";
import HomeLanes from "./HomeLanes";

afterEach(() => {
  vi.restoreAllMocks();
});

const lanesPayload = {
  continue: { lesson_id: "fractions-compare", lane: "hesi", title: "Comparing fractions", session_id: null, label: "Continue: Comparing fractions" },
  lanes: [
    { lane_id: "dsa", title: "Algorithms", blurb: "DSA lane", status: "available", lessons: [{ lesson_id: "sliding-window-box", title: "Sliding window: the box", state: "not_started", progress: { done: 0, total: 6 } }], legacy: { kind: "dsa_pir" as const, label: "Classic sliding-window lesson" } },
    { lane_id: "hesi", title: "HESI A2 prep", blurb: "HESI lane", status: "available", lessons: [{ lesson_id: "fractions-compare", title: "Comparing fractions", state: "not_started", progress: { done: 0, total: 6 } }], legacy: { kind: "hesi_topics" as const, label: "Practice HESI topics" } },
    { lane_id: "ai", title: "AI from scratch", blurb: "AI lane", status: "in_progress_content", lessons: [], legacy: null },
    { lane_id: "study-os", title: "Study OS", blurb: "Study OS lane", status: "available", lessons: [{ lesson_id: "welcome", title: "Welcome", state: "done", progress: { done: 1, total: 1 } }], legacy: null },
  ],
};

describe("HomeLanes", () => {
  it("renders all 4 lanes and exactly one primary Continue button", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((url: string) => {
      if (url === "/api/lanes") {
        return Promise.resolve(new Response(JSON.stringify(lanesPayload), { status: 200 }));
      }
      if (url === "/api/home") {
        return Promise.resolve(new Response(JSON.stringify({ handle: "a", display_name: null, streak_days: 0, dsa: { current_step: null, status: null }, hesi: { sections: [], recommended_topic: null, reviews_due: 0, content_status: "" } }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ error: "not found" }), { status: 404 }));
    }));

    const { container, cleanup } = render(<HomeLanes />);
    await new Promise((r) => setTimeout(r, 20));

    const cards = container.querySelectorAll(".lane-card");
    expect(cards.length).toBe(4);

    const continueButtons = container.querySelectorAll(".continue-btn");
    expect(continueButtons.length).toBe(1);
    expect(continueButtons[0].textContent).toBe("Continue: Comparing fractions");

    cleanup();
  });
});
