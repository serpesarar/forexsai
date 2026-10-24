import { afterEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "../auth/store";
import { authenticatedFetch } from "../api/authenticatedFetch";

afterEach(() => { vi.unstubAllGlobals(); useAuthStore.setState({ token: null }); });

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
});
