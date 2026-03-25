import { afterEach, describe, expect, it } from "vitest";
import { buildApiUrl, buildWebSocketUrl, getApiBase, normalizeApiBase } from "../base";

const originalApiBase = process.env.NEXT_PUBLIC_API_URL;
const originalAllowCrossOriginApi = process.env.NEXT_PUBLIC_ALLOW_CROSS_ORIGIN_API;

afterEach(() => {
  process.env.NEXT_PUBLIC_API_URL = originalApiBase;
  process.env.NEXT_PUBLIC_ALLOW_CROSS_ORIGIN_API = originalAllowCrossOriginApi;
});

describe("api base normalization", () => {
  it("falls back to same-origin when env is empty", () => {
    process.env.NEXT_PUBLIC_API_URL = "";
    expect(getApiBase()).toBe("");
  });

  it("adds https to protocol-less production hosts", () => {
    expect(normalizeApiBase("upbeat-flow-production.up.railway.app/")).toBe(
      "https://upbeat-flow-production.up.railway.app"
    );
  });

  it("uses http for localhost-style hosts", () => {
    expect(normalizeApiBase("localhost:8000/")).toBe("http://localhost:8000");
  });

  it("builds endpoint urls from the normalized base", () => {
    process.env.NEXT_PUBLIC_API_URL = "upbeat-flow-production.up.railway.app";
    expect(buildApiUrl("/api/learning/model-detail-analytics")).toBe(
      "https://upbeat-flow-production.up.railway.app/api/learning/model-detail-analytics"
    );
  });

  it("builds websocket urls from the normalized base", () => {
    process.env.NEXT_PUBLIC_API_URL = "localhost:8000";
    expect(buildWebSocketUrl("/ws/all")).toBe("ws://localhost:8000/ws/all");
  });

  it("keeps explicit cross-origin bases available for server-side helpers", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://upbeat-flow-production.up.railway.app";
    expect(getApiBase()).toBe("https://upbeat-flow-production.up.railway.app");
  });
});