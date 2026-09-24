import { describe, expect, it, vi } from "vitest";
import { Tracker, sanitizePath, type TrackEvent } from "./tracker";

describe("Tracker", () => {
  it("batches and flushes at maxBatch", async () => {
    const sent: TrackEvent[][] = [];
    const t = new Tracker((b) => { sent.push(b); }, { maxBatch: 3, flushMs: 10_000 });
    t.pageView("/");
    t.click("home.dsa");
    expect(sent).toHaveLength(0);
    t.click("home.topic");
    await Promise.resolve();
    expect(sent).toHaveLength(1);
    expect(sent[0].map((e) => e.type)).toEqual(["page_view", "click", "click"]);
    expect(sent[0].every((e) => e.client_session === t.clientSession)).toBe(true);
  });

  it("measures time on step and answer latency", async () => {
    let now = 1000;
    const sent: TrackEvent[][] = [];
    const t = new Tracker((b) => { sent.push(b); }, { now: () => now });
    t.stepShown("s-1", "t-1", "position.e0.n2");
    now = 4500;
    expect(t.stepAnswered()).toBe(3500);
    await t.flush();
    const types = sent[0].map((e) => e.type);
    expect(types).toEqual(["step_shown", "step_answered", "time_on_step"]);
    expect(sent[0][2].value_ms).toBe(3500);
    expect(sent[0][1].step_id).toBe("position.e0.n2");
  });

  it("drops unsafe paths and control ids", async () => {
    const sent: TrackEvent[][] = [];
    const t = new Tracker((b) => { sent.push(b); });
    t.track({ type: "click", control: "Bad Control!", path: "/lesson?email=a@b.c" });
    await t.flush();
    expect(sent[0][0].control).toBeUndefined();
    expect(sent[0][0].path).toBe("/lesson");
    expect(sanitizePath("javascript:alert(1)")).toBeUndefined();
  });

  it("never throws when the sender fails", async () => {
    const t = new Tracker(() => Promise.reject(new Error("offline")));
    t.pageView("/");
    await expect(t.flush()).resolves.toBeUndefined();
  });

  it("flushes on a timer", async () => {
    vi.useFakeTimers();
    const send = vi.fn();
    const t = new Tracker(send, { flushMs: 50 });
    t.pageView("/");
    vi.advanceTimersByTime(60);
    expect(send).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});
