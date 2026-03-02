/**
 * News-Chart Correlation System Types
 * Bidirectional binding between candlestick charts and news events
 */

// Core symbol types supported by the system
export type SupportedSymbol = 
  | "XAUUSD" 
  | "NASDAQ" 
  | "DAX" 
  | "USOIL" 
  | "VIX" 
  | "DXY" 
  | "EURUSD" 
  | "GBPUSD" 
  | "BTCUSD"
  | string;

// Direction of price impact
export type ImpactDirection = "bullish" | "bearish" | "neutral";

// Market sentiment classification
export type MarketSentiment = "risk_on" | "risk_off" | "neutral";

// Volatility expectation
export type VolatilityExpectation = "high" | "medium" | "low";

// Event duration classification
export type EventDuration = "immediate" | "short_term" | "long_term";

// Impact information for a specific symbol
export interface SymbolImpact {
  symbol: SupportedSymbol;
  direction: ImpactDirection;
  score: number; // 1-10
  confidence: number; // 0-1
  reasoning: string;
  emoji: string;
}

// Raw news input from data provider
export interface RawNews {
  id: string;
  timestamp: string; // ISO 8601
  source: string;
  headline: string;
  content?: string;
  category?: string;
  url?: string;
  imageUrl?: string;
}

// News urgency levels
export type NewsUrgency = "breaking" | "high" | "medium" | "low";

// AI-enriched news with impact analysis
export interface EnrichedNews extends RawNews {
  impacts: SymbolImpact[];
  urgency: NewsUrgency;
  sentiment: MarketSentiment;
  volatilityExpectation: VolatilityExpectation;
  keyLevels?: {
    support?: number[];
    resistance?: number[];
  };
  eventDuration: EventDuration;
  affectedCandles: string[]; // ISO timestamps
  aiConfidence: number; // 0-100
  analysisTimestamp: string;
}

// Chart marker for news events
export interface NewsMarker {
  time: number; // Unix timestamp (seconds)
  position: "aboveBar" | "belowBar";
  color: string;
  shape: "circle" | "square" | "arrowUp" | "arrowDown";
  size: number;
  newsIds: string[];
  tooltip: string;
  impactCount: number;
  symbol?: SupportedSymbol; // For ghost markers
  isGhost?: boolean; // Indirect relationship marker
}

// Candle data structure
export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

// Correlation state for Zustand store
export interface CorrelationState {
  // Selection state
  selectedCandle: CandleData | null;
  selectedNewsIds: string[];
  highlightedTimeRange: { start: number; end: number } | null;
  hoveredNewsId: string | null;
  
  // Data
  news: EnrichedNews[];
  markers: NewsMarker[];
  isLoading: boolean;
  error: string | null;
  
  // Filters
  filters: {
    impactLevel: "all" | "high" | "medium" | "low";
    affectedSymbols: SupportedSymbol[];
    sentiment: "all" | "bullish" | "bearish" | "neutral";
    timeRange: { start: number; end: number } | null;
  };
  
  // Actions
  selectCandle: (candle: CandleData | null) => void;
  selectNews: (newsId: string) => void;
  deselectNews: (newsId: string) => void;
  clearSelection: () => void;
  highlightTimeRange: (range: { start: number; end: number } | null) => void;
  setHoveredNews: (newsId: string | null) => void;
  setNews: (news: EnrichedNews[]) => void;
  setMarkers: (markers: NewsMarker[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilter: <K extends keyof CorrelationState["filters"]>(
    key: K,
    value: CorrelationState["filters"][K]
  ) => void;
  addNews: (news: EnrichedNews) => void;
  removeNews: (newsId: string) => void;
}

// API response types
export interface NewsAnalysisResponse {
  success: boolean;
  data?: EnrichedNews;
  error?: string;
}

export interface NewsListResponse {
  success: boolean;
  data: EnrichedNews[];
  total: number;
  page: number;
  limit: number;
}

export interface CorrelatedNewsRequest {
  symbol: SupportedSymbol;
  timeframe: string;
  startTime?: number;
  endTime?: number;
  impactFilter?: "all" | "high" | "medium" | "low";
}

// Chart configuration
export interface ChartConfig {
  symbol: SupportedSymbol;
  timeframe: string;
  showGhostMarkers: boolean;
  markerSize: number;
  enableAnimations: boolean;
  heatmapOverlay: boolean;
}

// News card display props
export interface NewsCardProps {
  news: EnrichedNews;
  isSelected: boolean;
  isHighlighted: boolean;
  currentSymbol: SupportedSymbol;
  onClick: () => void;
  onHover: () => void;
  onLeave: () => void;
}

// Impact badge props
export interface ImpactBadgeProps {
  impact: SymbolImpact;
  showScore?: boolean;
  showConfidence?: boolean;
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  onClick?: () => void;
}

// WebSocket message types
export interface NewsWebSocketMessage {
  type: "news" | "update" | "delete";
  data: EnrichedNews | { id: string };
  timestamp: string;
}

// AI Analysis request/response
export interface AIAnalysisRequest {
  headline: string;
  content?: string;
  timestamp: string;
  source?: string;
}

export interface AIAnalysisResponse {
  impacts: SymbolImpact[];
  sentiment: MarketSentiment;
  volatilityExpectation: VolatilityExpectation;
  keyLevels?: {
    support?: number[];
    resistance?: number[];
  };
  eventDuration: EventDuration;
  confidence: number;
}

// Historical correlation tracking
export interface CorrelationTracking {
  newsId: string;
  symbol: SupportedSymbol;
  predictedDirection: ImpactDirection;
  predictedScore: number;
  actualDirection?: ImpactDirection;
  actualMovement?: number;
  verifiedAt?: string;
  accuracy?: number; // Calculated field
}

// Filter options
export interface NewsFilterOptions {
  symbols: SupportedSymbol[];
  impactLevels: Array<{ value: string; label: string }>;
  sentiments: Array<{ value: string; label: string }>;
  timeRanges: Array<{ value: string; label: string; hours: number }>;
}
