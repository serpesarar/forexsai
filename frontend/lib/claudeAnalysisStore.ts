import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ClaudeAnalysisState {
  analysisData: Record<string, any>;
  detailedData: Record<string, any>;
  lastUpdated: Record<string, string>;
  setAnalysis: (symbol: string, data: any) => void;
  setDetailed: (symbol: string, data: any) => void;
  getAnalysis: (symbol: string) => any;
  getDetailed: (symbol: string) => any;
  getLastUpdated: (symbol: string) => string | null;
}

export const useClaudeAnalysisStore = create<ClaudeAnalysisState>()(
  persist(
    (set, get) => ({
      analysisData: {},
      detailedData: {},
      lastUpdated: {},
      
      setAnalysis: (symbol, data) => set((state) => ({
        analysisData: { ...state.analysisData, [symbol]: data },
        lastUpdated: { ...state.lastUpdated, [symbol]: new Date().toISOString() }
      })),
      
      setDetailed: (symbol, data) => set((state) => ({
        detailedData: { ...state.detailedData, [symbol]: data },
        lastUpdated: { ...state.lastUpdated, [symbol]: new Date().toISOString() }
      })),
      
      getAnalysis: (symbol) => get().analysisData[symbol] || null,
      getDetailed: (symbol) => get().detailedData[symbol] || null,
      getLastUpdated: (symbol) => get().lastUpdated[symbol] || null,
    }),
    { name: "claude-analysis-storage" }
  )
);
