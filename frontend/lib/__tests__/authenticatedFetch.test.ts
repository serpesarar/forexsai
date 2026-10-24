import { afterEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "../auth/store";
import { authenticatedFetch } from "../api/authenticatedFetch";

afterEach(() => { vi.unstubAllGlobals(); useAuthStore.setState({ token: null, user: null, isAuthenticated: false }); });

describe("authenticated operational requests", () => {
  it("reads the current token per request and preserves JSON headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}"));
    vi.stubGlobal("fetch", fetchMock);
    useAuthStore.setState({ token: "first-session" });
    await authenticatedFetch("https://api.example.test/api/evolution/registry", {
      headers: { "Content-Type": "application/json" },
    });
    useAuthStore.setState({ token: "second-session" });
    await authenticatedFetch("https://api.example.test/api/evolution/registry");
    expect(fetchMock.mock.calls[0][1].headers.get("Authorization")).toBe("Bearer first-session");
    expect(fetchMock.mock.calls[0][1].headers.get("Content-Type")).toBe("application/json");
    expect(fetchMock.mock.calls[1][1].headers.get("Authorization")).toBe("Bearer second-session");
    expect(fetchMock.mock.calls[0][0]).not.toContain("session");
  });
  it("does not invent a token for a signed-out visitor", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}"));
    vi.stubGlobal("fetch", fetchMock);
    await authenticatedFetch("https://api.example.test/api/admin/report");
    expect(fetchMock.mock.calls[0][1].headers.has("Authorization")).toBe(false);
  });

  it("clears a rejected session so protected pages can return to sign-in", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
    useAuthStore.setState({ token: "expired-session", isAuthenticated: true });
    const response = await authenticatedFetch("https://api.example.test/api/evolution/overview");
    expect(response.status).toBe(401);
    expect(useAuthStore.getState()).toMatchObject({ token: null, user: null, isAuthenticated: false });
  });

  it("keeps a newer session when an older request returns 401", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => {
      useAuthStore.setState({ token: "new-session", isAuthenticated: true });
      return new Response(null, { status: 401 });
    }));
    useAuthStore.setState({ token: "old-session", isAuthenticated: true });
    await authenticatedFetch("https://api.example.test/api/evolution/overview");
    expect(useAuthStore.getState()).toMatchObject({ token: "new-session", isAuthenticated: true });
  });

  it("keeps the session for permission failures and server errors", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(null, { status: 403 }))
      .mockResolvedValueOnce(new Response(null, { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);
    useAuthStore.setState({ token: "valid-session", isAuthenticated: true });
    await authenticatedFetch("https://api.example.test/api/admin/metrics");
    await authenticatedFetch("https://api.example.test/api/admin/metrics");
    expect(useAuthStore.getState()).toMatchObject({ token: "valid-session", isAuthenticated: true });
  });
});
