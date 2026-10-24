import React from "react";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import AuthGuard from "../AuthGuard";
import { useAuthStore } from "../../lib/auth/store";
import { authenticatedFetch } from "../../lib/api/authenticatedFetch";

const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
const originalCheckAuth = useAuthStore.getState().checkAuth;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  replace.mockClear();
  useAuthStore.setState({ token: null, user: null, isAuthenticated: false, checkAuth: originalCheckAuth });
});

it("returns a protected page to sign-in when its persisted session is rejected", async () => {
  useAuthStore.setState({ token: "expired-session", isAuthenticated: true,
    _hasHydrated: true, checkAuth: vi.fn().mockResolvedValue(true) });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
  render(<AuthGuard><div>Private dashboard</div></AuthGuard>);
  await screen.findByText("Private dashboard");
  await act(async () => { await authenticatedFetch("https://api.example.test/api/evolution/overview"); });
  await waitFor(() => expect(replace).toHaveBeenCalledWith("/welcome"));
  expect(screen.queryByText("Private dashboard")).toBeNull();
});
