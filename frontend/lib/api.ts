import { useQuery, useMutation } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }
  return response.json() as Promise<T>;
}

export function useRunAll() {
  return useMutation({
    mutationFn: () => fetcher("/api/run/all", { method: "POST" })
  });
}

export function useNasdaq() {
  return useQuery({
    queryKey: ["nasdaq"],
    queryFn: () => fetcher("/api/run/nasdaq", { method: "POST", body: "{}" }),
    staleTime: 300000
  });
}

export function useXauusd() {
  return useQuery({
    queryKey: ["xauusd"],
    queryFn: () => fetcher("/api/run/xauusd", { method: "POST", body: "{}" }),
    staleTime: 300000
  });
}

export function usePatternEngine(payload: { last_n: number; select_top: number; output_selected_only: boolean }) {
  return useQuery({
    queryKey: ["pattern-engine", payload],
    queryFn: () =>
      fetcher("/api/run/pattern-engine", {
        method: "POST",
        body: JSON.stringify(payload)
      }),
    staleTime: 300000
  });
}

export function useClaudePatterns(payload: { symbol: string; timeframes: string[] }) {
  return useQuery({
    queryKey: ["claude-patterns", payload],
    queryFn: () =>
      fetcher("/api/claude/analyze-patterns", {
        method: "POST",
        body: JSON.stringify(payload)
      }),
    staleTime: 300000
  });
}

export function useClaudeSentiment() {
  return useQuery({
    queryKey: ["claude-sentiment"],
    queryFn: () => fetcher("/api/claude/analyze-sentiment", { method: "POST", body: "{}" }),
    staleTime: 300000
  });
}
