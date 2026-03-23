import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useRefreshAge } from "../useRefreshAge";

describe("useRefreshAge", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-23T18:00:00.000Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("increments elapsed time from the initial refresh time", () => {
    const { result } = renderHook(() => useRefreshAge(new Date("2026-03-23T18:00:00.000Z")));

    expect(result.current.refreshAge).toBe("00:00");

    act(() => {
      vi.advanceTimersByTime(65000);
    });

    expect(result.current.refreshAge).toBe("01:05");
  });

  it("resets the timer when markRefreshed is called", () => {
    const { result } = renderHook(() => useRefreshAge(new Date("2026-03-23T18:00:00.000Z")));

    act(() => {
      vi.advanceTimersByTime(30000);
    });

    expect(result.current.refreshAge).toBe("00:30");

    act(() => {
      vi.setSystemTime(new Date("2026-03-23T18:00:30.000Z"));
      result.current.markRefreshed();
    });

    expect(result.current.refreshAge).toBe("00:00");

    act(() => {
      vi.advanceTimersByTime(10000);
    });

    expect(result.current.refreshAge).toBe("00:10");
  });
});
