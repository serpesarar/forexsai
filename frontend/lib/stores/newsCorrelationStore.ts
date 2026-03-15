"use client";

import { create } from "zustand";

interface NewsCorrelationStoreState {
  selectedSymbol: string;
  symbols: string[];
  setSelectedSymbol: (symbol: string) => void;
}

const defaultSymbols = [
  "XAUUSD",
  "NASDAQ",
  "DAX",
  "USOIL",
];

export const useNewsCorrelationStore = create<NewsCorrelationStoreState>((set) => ({
  selectedSymbol: "XAUUSD",
  symbols: defaultSymbols,
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
}));
