import { create } from "zustand";

export type ChartTimeframe = "5m" | "15m" | "1h" | "4h" | "1d";

interface DashboardState {
  autoRefresh: "off" | "30s" | "60s";
  lastUpdated?: string;
  setAutoRefresh: (value: DashboardState["autoRefresh"]) => void;
  setLastUpdated: (value: string) => void;
}

interface ChartState {
  symbol: string;
  timeframe: ChartTimeframe;
  setSymbol: (value: string) => void;
  setTimeframe: (value: ChartTimeframe) => void;
}

interface NewsState {
  impactFilter: "all" | "high" | "medium" | "low";
  categoryFilter: "all" | "fed" | "inflation" | "jobs";
  setImpactFilter: (value: NewsState["impactFilter"]) => void;
  setCategoryFilter: (value: NewsState["categoryFilter"]) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  autoRefresh: "off",
  lastUpdated: undefined,
  setAutoRefresh: (value) => set({ autoRefresh: value }),
  setLastUpdated: (value) => set({ lastUpdated: value })
}));

export const useChartStore = create<ChartState>((set) => ({
  symbol: "NDX.INDX",
  timeframe: "5m",
  setSymbol: (value) => set({ symbol: value }),
  setTimeframe: (value) => set({ timeframe: value })
}));

export const useNewsStore = create<NewsState>((set) => ({
  impactFilter: "all",
  categoryFilter: "all",
  setImpactFilter: (value) => set({ impactFilter: value }),
  setCategoryFilter: (value) => set({ categoryFilter: value })
}));
