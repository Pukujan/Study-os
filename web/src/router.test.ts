import { describe, expect, it } from "vitest";
import { matchRoute } from "./router";

describe("router new routes", () => {
  it("matches /play/:uuid", () => {
    const id = "0b9a3f5e-1111-4222-8333-444455556666";
    expect(matchRoute(`/play/${id}`)).toEqual({ name: "play", id });
  });

  it("rejects invalid play ids", () => {
    expect(matchRoute("/play/not-a-uuid")).toEqual({ name: "notfound" });
  });

  it("matches /try", () => {
    expect(matchRoute("/try")).toEqual({ name: "try" });
  });

  it("matches /admin/feedback", () => {
    expect(matchRoute("/admin/feedback")).toEqual({ name: "admin_feedback" });
  });
});
