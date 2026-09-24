import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, mutationHeaders, setCsrf } from "./api";
import { matchRoute } from "./router";

afterEach(() => {
  vi.restoreAllMocks();
  setCsrf(null);
});

describe("api", () => {
  it("sends the required headers on mutations", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ handle: "a", display_name: null, role: "learner", csrf_token: "tok" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await api.login("a@example.com", "correct horse battery");
    expect(mutationHeaders()["X-CSRF-Token"]).toBe("tok");
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>)["X-Study-OS"]).toBe("1");
    expect(init.credentials).toBe("same-origin");
  });

  it("maps error bodies to ApiError codes", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: "rate_limited" }), { status: 429 })));
    await expect(api.home()).rejects.toEqual(new ApiError(429, "rate_limited"));
  });
});

describe("router", () => {
  it("matches routes", () => {
    expect(matchRoute("/")).toEqual({ name: "home" });
    expect(matchRoute("/login")).toEqual({ name: "login" });
    const id = "0b9a3f5e-1111-4222-8333-444455556666";
    expect(matchRoute(`/lesson/${id}`)).toEqual({ name: "lesson", id });
    expect(matchRoute("/lesson/../etc")).toEqual({ name: "notfound" });
  });
});
