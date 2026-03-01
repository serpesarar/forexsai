/**
 * Mock data generator for News-Chart Correlation System
 * Used for development and testing without API dependencies
 */

import type { 
  EnrichedNews, 
  CandleData, 
  SupportedSymbol,
  NewsMarker,
  AIAnalysisResponse 
} from "@/types/news-correlation";

// Mock news headlines
const mockHeadlines = [
  "Trump threatens Iran with military action if nuclear deal fails",
  "Fed signals potential rate cuts in coming months",
  "ECB holds rates steady amid inflation concerns",
  "US Non-Farm Payrolls beat expectations, adds 250k jobs",
  "Gold hits new all-time high as safe haven demand surges",
  "Oil prices spike on Middle East supply fears",
  "Bitcoin ETF approval drives crypto markets higher",
  "Dollar strengthens on hawkish Fed comments",
  "Euro zone inflation rises, backing ECB's case to keep rates on hold",
  "VIX jumps as geopolitical tensions escalate",
];

// Mock sources
const mockSources = ["Bloomberg", "Reuters", "CNBC", "Financial Times", "MarketWatch", "WSJ"];

// Generate random timestamp within last 24 hours
const generateRandomTimestamp = (): string => {
  const now = new Date();
  const hoursAgo = Math.random() * 24;
  const timestamp = new Date(now.getTime() - hoursAgo * 60 * 60 * 1000);
  return timestamp.toISOString();
};

// Generate mock AI analysis
const generateMockAnalysis = (headline: string): AIAnalysisResponse => {
  const lowerHeadline = headline.toLowerCase();
  
  // Rule-based mock analysis
  if (lowerHeadline.includes("iran") || lowerHeadline.includes("military")) {
    return {
      impacts: [
        { symbol: "XAUUSD", direction: "bullish", score: 8, confidence: 0.85, reasoning: "Safe haven demand increases", emoji: "🚀" },
        { symbol: "USOIL", direction: "bullish", score: 7, confidence: 0.80, reasoning: "Supply disruption risk", emoji: "📈" },
        { symbol: "VIX", direction: "bullish", score: 6, confidence: 0.75, reasoning: "Geopolitical uncertainty", emoji: "⚠️" },
        { symbol: "NASDAQ", direction: "bearish", score: 5, confidence: 0.70, reasoning: "Risk-off sentiment", emoji: "📉" },
      ],
      sentiment: "risk_off",
      volatilityExpectation: "high",
      keyLevels: { support: [2900, 2880], resistance: [2950, 2980] },
      eventDuration: "short_term",
      confidence: 82,
    };
  }
  
  if (lowerHeadline.includes("fed") || lowerHeadline.includes("rate")) {
    const isHawkish = lowerHeadline.includes("hawkish") || lowerHeadline.includes("raise");
    return {
      impacts: [
        { symbol: "DXY", direction: isHawkish ? "bullish" : "bearish", score: 8, confidence: 0.88, reasoning: isHawkish ? "Rate hikes strengthen USD" : "Rate cuts weaken USD", emoji: isHawkish ? "🚀" : "📉" },
        { symbol: "XAUUSD", direction: isHawkish ? "bearish" : "bullish", score: 7, confidence: 0.82, reasoning: isHawkish ? "Higher rates hurt gold" : "Lower rates help gold", emoji: isHawkish ? "📉" : "🚀" },
        { symbol: "NASDAQ", direction: isHawkish ? "bearish" : "bullish", score: 7, confidence: 0.80, reasoning: isHawkish ? "Higher rates hurt tech stocks" : "Lower rates help growth stocks", emoji: isHawkish ? "📉" : "🚀" },
      ],
      sentiment: isHawkish ? "risk_off" : "risk_on",
      volatilityExpectation: "high",
      keyLevels: undefined,
      eventDuration: "long_term",
      confidence: 85,
    };
  }
  
  if (lowerHeadline.includes("gold") || lowerHeadline.includes("all-time high")) {
    return {
      impacts: [
        { symbol: "XAUUSD", direction: "bullish", score: 9, confidence: 0.90, reasoning: "New all-time high momentum", emoji: "🚀" },
        { symbol: "DXY", direction: "bearish", score: 5, confidence: 0.60, reasoning: "Inverse correlation", emoji: "📉" },
      ],
      sentiment: "neutral",
      volatilityExpectation: "high",
      keyLevels: { support: [2900], resistance: [2950, 3000] },
      eventDuration: "short_term",
      confidence: 88,
    };
  }
  
  if (lowerHeadline.includes("oil") || lowerHeadline.includes("supply")) {
    return {
      impacts: [
        { symbol: "USOIL", direction: "bullish", score: 7, confidence: 0.78, reasoning: "Supply concerns drive prices up", emoji: "📈" },
        { symbol: "XAUUSD", direction: "bullish", score: 4, confidence: 0.55, reasoning: "Indirect inflation hedge", emoji: "➡️" },
      ],
      sentiment: "risk_off",
      volatilityExpectation: "medium",
      keyLevels: undefined,
      eventDuration: "short_term",
      confidence: 72,
    };
  }
  
  if (lowerHeadline.includes("bitcoin") || lowerHeadline.includes("crypto")) {
    return {
      impacts: [
        { symbol: "BTCUSD", direction: "bullish", score: 8, confidence: 0.82, reasoning: "ETF approval positive for adoption", emoji: "🚀" },
        { symbol: "NASDAQ", direction: "bullish", score: 4, confidence: 0.60, reasoning: "Tech correlation", emoji: "➡️" },
      ],
      sentiment: "risk_on",
      volatilityExpectation: "high",
      keyLevels: undefined,
      eventDuration: "long_term",
      confidence: 75,
    };
  }
  
  // Default random analysis
  const symbols: SupportedSymbol[] = ["XAUUSD", "NASDAQ", "DAX", "USOIL", "VIX"];
  const directions: Array<"bullish" | "bearish" | "neutral"> = ["bullish", "bearish", "neutral"];
  
  return {
    impacts: symbols.slice(0, 2 + Math.floor(Math.random() * 2)).map(sym => ({
      symbol: sym,
      direction: directions[Math.floor(Math.random() * directions.length)],
      score: 3 + Math.floor(Math.random() * 5),
      confidence: 0.5 + Math.random() * 0.3,
      reasoning: "General market impact",
      emoji: ["📈", "📉", "➡️"][Math.floor(Math.random() * 3)],
    })),
    sentiment: ["risk_on", "risk_off", "neutral"][Math.floor(Math.random() * 3)] as any,
    volatilityExpectation: ["high", "medium", "low"][Math.floor(Math.random() * 3)] as any,
    keyLevels: undefined,
    eventDuration: "short_term",
    confidence: 50 + Math.floor(Math.random() * 30),
  };
};

// Generate mock enriched news
export const generateMockEnrichedNews = (count: number = 10): EnrichedNews[] => {
  return Array.from({ length: count }, (_, i) => {
    const headline = mockHeadlines[i % mockHeadlines.length];
    const analysis = generateMockAnalysis(headline);
    const timestamp = generateRandomTimestamp();
    
    return {
      id: `news_${Date.now()}_${i}`,
      timestamp,
      source: mockSources[Math.floor(Math.random() * mockSources.length)],
      headline,
      content: `Full article content for: ${headline}. This is a mock news article for testing purposes.`,
      category: ["Geopolitical", "Economic", "Central Bank", "Market"][Math.floor(Math.random() * 4)],
      impacts: analysis.impacts.map(imp => ({
        symbol: imp.symbol,
        direction: imp.direction,
        score: imp.score,
        confidence: imp.confidence,
        reasoning: imp.reasoning,
        emoji: imp.emoji || "📊",
      })),
      sentiment: analysis.sentiment,
      volatilityExpectation: analysis.volatilityExpectation,
      keyLevels: analysis.keyLevels,
      eventDuration: analysis.eventDuration,
      affectedCandles: [],
      aiConfidence: analysis.confidence,
      analysisTimestamp: timestamp,
    };
  }).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
};

// Generate mock candle data
export const generateMockCandles = (
  symbol: SupportedSymbol = "XAUUSD",
  timeframe: string = "1h",
  bars: number = 200
): CandleData[] => {
  const candles: CandleData[] = [];
  const now = new Date();
  
  // Base price based on symbol
  const basePrices: Record<string, number> = {
    XAUUSD: 2900,
    NASDAQ: 18500,
    DAX: 22500,
    USOIL: 75,
    VIX: 15,
    DXY: 104,
    EURUSD: 1.08,
    GBPUSD: 1.26,
    BTCUSD: 65000,
  };
  
  let currentPrice = basePrices[symbol] || 100;
  
  for (let i = bars; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    
    // Random price movement
    const volatility = symbol === "VIX" ? 0.5 : symbol === "BTCUSD" ? 0.02 : 0.005;
    const change = (Math.random() - 0.5) * 2 * volatility * currentPrice;
    
    const open = currentPrice;
    const close = currentPrice + change;
    const high = Math.max(open, close) + Math.random() * Math.abs(change) * 0.5;
    const low = Math.min(open, close) - Math.random() * Math.abs(change) * 0.5;
    
    candles.push({
      time: Math.floor(time.getTime() / 1000),
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume: Math.floor(Math.random() * 10000) + 1000,
    });
    
    currentPrice = close;
  }
  
  return candles;
};

// Generate mock markers from news
export const generateMockMarkers = (
  news: EnrichedNews[],
  symbol: SupportedSymbol
): NewsMarker[] => {
  const markerMap = new Map<number, NewsMarker>();
  
  news.forEach((item) => {
    const symbolImpact = item.impacts.find(
      (i) => i.symbol === symbol || i.symbol === "*"
    );
    
    const hasGhostImpact = item.impacts.some(
      (i) => i.symbol !== symbol && i.symbol !== "*"
    );
    
    if (!symbolImpact && !hasGhostImpact) return;
    
    const time = new Date(item.timestamp).getTime() / 1000;
    
    let color = "#eab308";
    let shape: NewsMarker["shape"] = "circle";
    let position: NewsMarker["position"] = "aboveBar";
    
    if (symbolImpact) {
      switch (symbolImpact.direction) {
        case "bullish":
          color = "#22c55e";
          shape = "arrowUp";
          position = "belowBar";
          break;
        case "bearish":
          color = "#ef4444";
          shape = "arrowDown";
          position = "aboveBar";
          break;
        case "neutral":
          color = "#eab308";
          shape = "square";
          break;
      }
    }
    
    if (item.volatilityExpectation === "high") {
      color = "#f59e0b";
      shape = "square";
    }
    
    const existing = markerMap.get(time);
    if (existing) {
      existing.newsIds.push(item.id);
      existing.impactCount += symbolImpact ? 1 : 0;
      existing.tooltip = `${existing.newsIds.length} news events`;
      if (symbolImpact && symbolImpact.score > 7) {
        existing.color = color;
      }
    } else {
      markerMap.set(time, {
        time,
        position,
        color,
        shape,
        size: symbolImpact?.score ? Math.min(8 + symbolImpact.score, 20) : 10,
        newsIds: [item.id],
        tooltip: item.headline.substring(0, 50) + "...",
        impactCount: symbolImpact ? 1 : 0,
        isGhost: !symbolImpact,
        symbol: !symbolImpact ? item.impacts[0]?.symbol : undefined,
      });
    }
  });
  
  return Array.from(markerMap.values()).sort((a, b) => a.time - b.time);
};

// Mock API response delay
export const mockDelay = (ms: number = 500): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

// Export all mock generators
export const mockNewsCorrelationAPI = {
  getCorrelatedNews: async (symbol: SupportedSymbol, timeframe: string): Promise<EnrichedNews[]> => {
    await mockDelay(300);
    return generateMockEnrichedNews(15);
  },
  
  getChartData: async (symbol: SupportedSymbol, timeframe: string, bars: number = 200): Promise<CandleData[]> => {
    await mockDelay(400);
    return generateMockCandles(symbol, timeframe, bars);
  },
  
  analyzeNews: async (headline: string, content?: string): Promise<AIAnalysisResponse> => {
    await mockDelay(800);
    return generateMockAnalysis(headline);
  },
};

export default mockNewsCorrelationAPI;
