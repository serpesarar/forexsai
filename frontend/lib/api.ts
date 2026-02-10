import { useQuery, useMutation } from "@tanstack/react-query";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

export async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
      signal: controller.signal,
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "Request failed");
    }
    return response.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
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
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 15000
  });
}

export function useXauusd() {
  return useQuery({
    queryKey: ["xauusd"],
    queryFn: () => fetcher("/api/run/xauusd", { method: "POST", body: "{}" }),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 15000
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
    refetchInterval: 60000, // Auto-refresh every 60 seconds
    staleTime: 30000
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
    refetchInterval: 60000, // Auto-refresh every 60 seconds
    staleTime: 30000
  });
}

export function useClaudeSentiment() {
  return useQuery({
    queryKey: ["claude-sentiment"],
    queryFn: () => fetcher("/api/claude/analyze-sentiment", { method: "POST", body: "{}" }),
    refetchInterval: 60000, // Auto-refresh every 60 seconds  
    staleTime: 30000
  });
}
export async function submitReport(payload: { type: string; message: string; email?: string, user_id?: string }) {
  return fetcher("/api/admin/report", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function useAdminMetrics() {
  return useQuery({
    queryKey: ["admin-metrics"],
    queryFn: () => fetcher<{ total_users: number, active_users_24h: number, total_reports: number, pending_reports: number }>("/api/admin/metrics"),
    refetchInterval: 60000,
  });
}

export function useAdminReports() {
  return useQuery({
    queryKey: ["admin-reports"],
    queryFn: () => fetcher<any[]>("/api/admin/reports"),
    refetchInterval: 30000,
  });
}
