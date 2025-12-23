import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
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

export function useRtyhiimDetect() {
  return useQuery({
    queryKey: ["rtyhiim"],
    queryFn: () => fetcher("/api/rtyhiim/detect", { method: "POST", body: "{}" }),
    staleTime: 300000
  });
}
