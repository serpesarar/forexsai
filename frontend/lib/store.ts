import { create } from "zustand";

export type ChartTimeframe = "5m" | "15m" | "1h" | "4h" | "1d";

type DetailPanelType = "support_resistance" | "ema_distance" | "trend_channel";

interface DashboardState {
  data: unknown | null;
  isLoading: boolean;
  autoRefresh: boolean;
  customAnalysis: { summary: string; insights: string[] } | null;
  customAnalysisLoading: boolean;
  fetchAll: () => Promise<void>;
  toggleAutoRefresh: (enabled: boolean) => void;
  runCustomAnalysis: () => Promise<void>;
}

interface DetailPanelState {
  isOpen: boolean;
  type: DetailPanelType | null;
  symbol: "NASDAQ" | "XAUUSD" | null;
  title: string;
  data: Record<string, any> | null;
  open: (type: DetailPanelType, data: Record<string, any>, symbol: "NASDAQ" | "XAUUSD", title: string) => void;
  close: () => void;
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

const customAnalysisMock = {
  summary: "NASDAQ momentum accelerating while XAUUSD remains range-bound.",
  insights: [
    "15m structure shows bullish continuation patterns on NDX.",
    "1h gold structure lacks follow-through; consider mean reversion.",
    "Cross-asset correlation indicates risk-on sentiment.",
  ],
};

export const useDashboardStore = create<DashboardState>((set, get) => ({
  data: null,
  isLoading: false,
  autoRefresh: false,
  customAnalysis: null,
  customAnalysisLoading: false,
  fetchAll: async () => {
    set({ isLoading: true });
    await new Promise((resolve) => setTimeout(resolve, 600));
    set({
      isLoading: false,
      data: {},
    });
  },
  toggleAutoRefresh: (enabled) => {
    set({ autoRefresh: enabled });
    if (enabled) {
      get().fetchAll();
    }
  },
  runCustomAnalysis: async () => {
    set({ customAnalysisLoading: true });
    await new Promise((resolve) => setTimeout(resolve, 900));
    set({ customAnalysisLoading: false, customAnalysis: customAnalysisMock });
  },
}));

export const useDetailPanelStore = create<DetailPanelState>((set) => ({
  isOpen: false,
  type: null,
  symbol: null,
  title: "",
  data: null,
  open: (type, data, symbol, title) => set({ isOpen: true, type, data, symbol, title }),
  close: () => set({ isOpen: false, type: null, data: null, symbol: null, title: "" }),
}));

export const useChartStore = create<ChartState>((set) => ({
  symbol: "NDX.INDX",
  timeframe: "5m",
  setSymbol: (value) => set({ symbol: value }),
  setTimeframe: (value) => set({ timeframe: value }),
}));

export const useNewsStore = create<NewsState>((set) => ({
  impactFilter: "all",
  categoryFilter: "all",
  setImpactFilter: (value) => set({ impactFilter: value }),
  setCategoryFilter: (value) => set({ categoryFilter: value }),
}));
