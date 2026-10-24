import { afterEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "../auth/store";
import { downloadBotTrades } from "../api/evolution";

afterEach(() => {
  vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers();
  useAuthStore.setState({ token: null });
});

describe("private trade CSV download", () => {
  it("downloads with authorization and releases its blob URL", async () => {
    vi.useFakeTimers();
    const makeUrl = vi.fn().mockReturnValue("blob:csv-test");
    const revokeUrl = vi.fn();
    const NativeURL = URL;
    vi.stubGlobal("URL", class extends NativeURL {
      static createObjectURL = makeUrl;
      static revokeObjectURL = revokeUrl;
    });
    const fetchMock = vi.fn().mockResolvedValue(new Response("ticket,net\n123,1"));
    vi.stubGlobal("fetch", fetchMock);
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    useAuthStore.setState({ token: "private-test-session" });
    await downloadBotTrades({ symbol: "NDX.INDX", start: "2026-10-01", end: "2026-10-23" });
    expect(fetchMock.mock.calls[0][1].headers.get("Authorization")).toBe("Bearer private-test-session");
    expect(fetchMock.mock.calls[0][0]).not.toContain("private-test-session");
    expect(click).toHaveBeenCalledOnce();
    expect(document.querySelector('a[href="blob:csv-test"]')).toBeNull();
    vi.runAllTimers();
    expect(revokeUrl).toHaveBeenCalledWith("blob:csv-test");
  });
  it("does not start a download when authorization fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("denied", { status: 401 })));
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    await expect(downloadBotTrades({})).rejects.toThrow("HTTP 401");
    expect(click).not.toHaveBeenCalled();
  });
});
