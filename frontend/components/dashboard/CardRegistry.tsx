"use client";

import React from "react";
import PatternEngineV2 from "../PatternEngineV2";
import MLPredictionPanel from "../MLPredictionPanel";
import ClaudeAnalysisPanel from "../ClaudeAnalysisPanel";
import OrderBlockPanel from "../OrderBlockPanel";
import RTYHIIMDetectorPanel from "../RTYHIIMDetectorPanel";
import TradingChartWrapper from "../TradingChartWrapper";

// Card size definitions
export type CardSize = "small" | "medium" | "large" | "full";

export interface CardDefinition {
  id: string;
  title: string;
  defaultColumn: "left" | "center" | "right";
  defaultOrder: number;
  defaultSize: CardSize;
  minSize: CardSize;
  component: React.ComponentType<any> | null; // null = custom render
  props?: Record<string, any>;
  gridSpan: {
    small: number;   // col-span
    medium: number;
    large: number;
    full: number;
  };
}

// All dashboard cards registry
export const CARD_REGISTRY: CardDefinition[] = [
  // Left Column - Signal Cards
  {
    id: "signal-nasdaq",
    title: "NASDAQ Trend",
    defaultColumn: "left",
    defaultOrder: 0,
    defaultSize: "medium",
    minSize: "small",
    component: null, // Custom render
    gridSpan: { small: 1, medium: 1, large: 1, full: 3 },
  },
  {
    id: "signal-xauusd",
    title: "XAUUSD Trend",
    defaultColumn: "left",
    defaultOrder: 1,
    defaultSize: "medium",
    minSize: "small",
    component: null,
    gridSpan: { small: 1, medium: 1, large: 1, full: 3 },
  },
  
  // Center Column - Analysis
  {
    id: "pattern-engine",
    title: "Pattern Engine V2",
    defaultColumn: "center",
    defaultOrder: 0,
    defaultSize: "large",
    minSize: "medium",
    component: PatternEngineV2,
    gridSpan: { small: 1, medium: 1, large: 2, full: 3 },
  },
  {
    id: "claude-patterns",
    title: "Claude Patterns",
    defaultColumn: "center",
    defaultOrder: 1,
    defaultSize: "medium",
    minSize: "small",
    component: null,
    gridSpan: { small: 1, medium: 1, large: 1, full: 3 },
  },
  
  // Right Column - Sentiment & News
  {
    id: "sentiment",
    title: "AI Sentiment",
    defaultColumn: "right",
    defaultOrder: 0,
    defaultSize: "medium",
    minSize: "small",
    component: null,
    gridSpan: { small: 1, medium: 1, large: 1, full: 3 },
  },
  {
    id: "news",
    title: "Market News",
    defaultColumn: "right",
    defaultOrder: 1,
    defaultSize: "medium",
    minSize: "small",
    component: null,
    gridSpan: { small: 1, medium: 1, large: 1, full: 3 },
  },
  
  // Full Width Cards
  {
    id: "ai-panels",
    title: "AI Tahmin Panelleri",
    defaultColumn: "center",
    defaultOrder: 2,
    defaultSize: "full",
    minSize: "large",
    component: null,
    gridSpan: { small: 1, medium: 2, large: 3, full: 3 },
  },
  {
    id: "order-blocks-nasdaq",
    title: "Order Blocks NASDAQ",
    defaultColumn: "center",
    defaultOrder: 3,
    defaultSize: "full",
    minSize: "large",
    component: OrderBlockPanel,
    props: { symbol: "NDX.INDX", symbolLabel: "NASDAQ" },
    gridSpan: { small: 1, medium: 2, large: 3, full: 3 },
  },
  {
    id: "order-blocks-xauusd",
    title: "Order Blocks XAUUSD",
    defaultColumn: "center",
    defaultOrder: 4,
    defaultSize: "full",
    minSize: "large",
    component: OrderBlockPanel,
    props: { symbol: "XAUUSD", symbolLabel: "XAUUSD" },
    gridSpan: { small: 1, medium: 2, large: 3, full: 3 },
  },
  {
    id: "rhythm-detectors",
    title: "Rhythm Detectors",
    defaultColumn: "center",
    defaultOrder: 5,
    defaultSize: "full",
    minSize: "large",
    component: null,
    gridSpan: { small: 1, medium: 2, large: 3, full: 3 },
  },
  {
    id: "charts",
    title: "Trading Charts",
    defaultColumn: "center",
    defaultOrder: 6,
    defaultSize: "full",
    minSize: "large",
    component: null,
    gridSpan: { small: 1, medium: 2, large: 3, full: 3 },
  },
];

// Helper to get card definition
export function getCardDefinition(cardId: string): CardDefinition | undefined {
  return CARD_REGISTRY.find(c => c.id === cardId);
}

// Get grid span class based on size
export function getGridSpanClass(cardId: string, size: CardSize): string {
  const card = getCardDefinition(cardId);
  if (!card) return "col-span-1";
  
  const span = card.gridSpan[size];
  switch (span) {
    case 1: return "col-span-1";
    case 2: return "md:col-span-2";
    case 3: return "md:col-span-2 lg:col-span-3";
    default: return "col-span-1";
  }
}
