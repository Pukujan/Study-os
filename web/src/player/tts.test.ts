import { afterEach, describe, expect, it, vi } from "vitest";
import { _resetTtsCache, loadTtsConfig } from "./tts";

describe("tts config", () => {
  afterEach(() => {
    _resetTtsCache();
    vi.unstubAllGlobals();
  });

  it("loads kokoro engine from /api/tts/config", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ engine: "kokoro", voice: "af_heart", speed: 1.08, kokoro: true }),
      })),
    );
    const cfg = await loadTtsConfig();
    expect(cfg.engine).toBe("kokoro");
    expect(cfg.voice).toBe("af_heart");
    expect(cfg.kokoro).toBe(true);
  });

  it("falls back to browser when config fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("offline");
      }),
    );
    const cfg = await loadTtsConfig();
    expect(cfg.engine).toBe("browser");
    expect(cfg.kokoro).toBe(false);
  });
});
