import { create } from "zustand";

interface DashboardState {
  autoRefresh: "off" | "30s" | "60s";
  lastUpdated?: string;
  setAutoRefresh: (value: DashboardState["autoRefresh"]) => void;
  setLastUpdated: (value: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  autoRefresh: "off",
  lastUpdated: undefined,
  setAutoRefresh: (value) => set({ autoRefresh: value }),
  setLastUpdated: (value) => set({ lastUpdated: value })
}));
