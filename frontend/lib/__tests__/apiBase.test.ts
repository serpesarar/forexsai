import { afterEach, describe, expect, it, vi } from "vitest";

import { getApiBase, normalizeApiBase } from "../api/base";

describe("api base helpers", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns localhost in development when NEXT_PUBLIC_API_URL is unset", () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");

    expect(getApiBase()).toBe("http://localhost:8000");
  });

  it("returns same-origin fallback when env is unset outside development", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");

    expect(getApiBase()).toBe("");
  });

  it("normalizes localhost-like values to http", () => {
    expect(normalizeApiBase("localhost:9000")).toBe("http://localhost:9000");
  });
});