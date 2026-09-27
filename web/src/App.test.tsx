import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import App from "./App";
import type { Me } from "./api";
import { render } from "./test-utils";

const guestMe: Me = { handle: "guest-abc123", display_name: null, role: "guest", csrf_token: "tok" };
const learnerMe: Me = { handle: "learner@example.com", display_name: "Alex", role: "learner", csrf_token: "tok" };

function stubFetch(me: Me) {
  const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    if (url === "/api/auth/me") return Promise.resolve(new Response(JSON.stringify(me), { status: 200 }));
    if (url === "/api/auth/config") {
      return Promise.resolve(new Response(JSON.stringify({ google: false, local_signup: true }), { status: 200 }));
    }
    if (url === "/api/auth/logout" && init?.method === "POST") {
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }
    if (url === "/api/events") return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    return Promise.resolve(new Response(JSON.stringify({ error: "not_found" }), { status: 404 }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function findButton(container: HTMLElement, label: string): HTMLButtonElement | undefined {
  return Array.from(container.querySelectorAll("button")).find((b) => b.textContent === label);
}

async function flush() {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 20));
  });
}

describe("App header", () => {
  beforeEach(() => {
    history.replaceState({}, "", "/try");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    history.replaceState({}, "", "/");
  });

  it("shows Sign out for a guest and clears the guest session", async () => {
    const fetchMock = stubFetch(guestMe);
    const { container, cleanup } = render(<App />);
    await flush();

    expect(findButton(container, "Save progress")).toBeTruthy();
    const signOut = findButton(container, "Sign out");
    expect(signOut).toBeTruthy();

    await act(async () => {
      signOut!.click();
    });
    await flush();

    const loggedOut = fetchMock.mock.calls.some(
      ([url, init]) => url === "/api/auth/logout" && (init as RequestInit | undefined)?.method === "POST",
    );
    expect(loggedOut).toBe(true);
    expect(location.pathname).toBe("/login");
    expect(findButton(container, "Sign out")).toBeUndefined();

    cleanup();
  });

  it("still shows Sign out for a non-guest account", async () => {
    stubFetch(learnerMe);
    const { container, cleanup } = render(<App />);
    await flush();

    expect(findButton(container, "Sign out")).toBeTruthy();
    expect(container.textContent).toContain("Alex");

    cleanup();
  });
});
