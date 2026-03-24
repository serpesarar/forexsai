import { useQuery } from "@tanstack/react-query";
import { buildApiUrl } from "./base";

export type DetailedDecision = "BUY" | "SELL" | "HOLD";

export interface DetailedAnalysisPayload {
  symbol: string;
  context: Record<string, any>;
  analysis: Record<string, any>;
}

async function fetchDetailedAIAnalysis(symbol: string): Promise<DetailedAnalysisPayload> {
  const res = await fetch(buildApiUrl(`/api/ai-analysis/detailed/${symbol}`));
  if (!res.ok) {
    throw new Error(`Failed to fetch detailed AI analysis for ${symbol}`);
  }
  return res.json();
}

export function useDetailedAIAnalysis(symbol: string) {
  return useQuery({
    queryKey: ["ai-analysis", "detailed", symbol],
    queryFn: () => fetchDetailedAIAnalysis(symbol),
    refetchInterval: 300000, // Auto refresh every 5 minutes
    staleTime: 30000, // Data is stale after 30 seconds (allows manual refresh)
    gcTime: 300000, // Keep in cache for 5 minutes
  });
}
