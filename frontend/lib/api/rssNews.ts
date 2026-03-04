/**
 * RSS News API Client
 * DeepSeek AI analizli haberler için API çağrıları
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://upbeat-flow-production.up.railway.app";

export interface NewsImpact {
  symbol: string;
  direction: "bullish" | "bearish" | "neutral";
  score: number;
  confidence: number;
  reasoning: string;
  reasoning_tr?: string;
  emoji?: string;
}

export interface RSSNewsItem {
  id: string;
  timestamp: string;
  source: string;
  headline: string;
  headline_tr?: string;
  content?: string;
  content_tr?: string;
  category: string;
  url: string;
  impacts: NewsImpact[];
  sentiment: "risk_on" | "risk_off" | "neutral";
  volatility_expectation: "high" | "medium" | "low";
  urgency: "breaking" | "high" | "medium" | "low";
  ai_confidence: number;
  duplicate_of?: string;
  sources: string[];
}

export interface RSSStats {
  period_hours: number;
  total_items: number;
  by_urgency: {
    breaking: number;
    high: number;
    medium: number;
    low: number;
  };
  by_sentiment: Record<string, number>;
  by_source: Record<string, number>;
  top_symbols: Record<string, number>;
}

// Tüm RSS haberlerini getir
export async function fetchRSSNews(
  hours: number = 24,
  limit: number = 50,
  symbol?: string
): Promise<RSSNewsItem[]> {
  const params = new URLSearchParams({
    hours: hours.toString(),
    limit: limit.toString(),
    skip_ai_filtered: "true",
  });

  if (symbol) {
    params.append("symbol", symbol);
  }

  const res = await fetch(`${API_BASE}/api/rss/news?${params}`);
  if (!res.ok) {
    throw new Error("Failed to fetch RSS news");
  }
  return res.json();
}

// Son breaking/high urgency haberleri getir
export async function fetchBreakingNews(limit: number = 10): Promise<RSSNewsItem[]> {
  const res = await fetch(`${API_BASE}/api/rss/latest-breaking?limit=${limit}`);
  if (!res.ok) {
    throw new Error("Failed to fetch breaking news");
  }
  const data = await res.json();
  return data.data || [];
}

// RSS istatistiklerini getir
export async function fetchRSSStats(hours: number = 24): Promise<RSSStats> {
  const res = await fetch(`${API_BASE}/api/rss/stats?hours=${hours}`);
  if (!res.ok) {
    throw new Error("Failed to fetch RSS stats");
  }
  return res.json();
}

// Kategori bazlı haberleri getir
export async function fetchNewsByCategory(
  category: string,
  hours: number = 24
): Promise<RSSNewsItem[]> {
  const res = await fetch(
    `${API_BASE}/api/rss/by-category/${category}?hours=${hours}`
  );
  if (!res.ok) {
    throw new Error("Failed to fetch news by category");
  }
  const data = await res.json();
  return data.data || [];
}

// Ekonomik takvim verilerini getir
export async function fetchEconomicCalendar(
  date?: string,
  currency?: string
): Promise<any[]> {
  const params = new URLSearchParams();
  if (date) params.append("date", date);
  if (currency) params.append("currency", currency);

  const res = await fetch(`${API_BASE}/api/rss/economic-calendar?${params}`);
  if (!res.ok) {
    throw new Error("Failed to fetch economic calendar");
  }
  const data = await res.json();
  return data.events || [];
}

// RSS sağlık durumunu kontrol et
export async function checkRSSDiagnostics(): Promise<{
  success: boolean;
  api_keys: {
    DEEP_SEEKR1: string;
    ANTHROPIC_API_KEY: string;
  };
  last_24h_stats: {
    total_news: number;
    ai_analyzed: number;
    fallback_analyzed: number;
    ai_ratio: string;
  };
}> {
  const res = await fetch(`${API_BASE}/api/rss/diagnostics`);
  if (!res.ok) {
    throw new Error("Failed to fetch RSS diagnostics");
  }
  return res.json();
}

// Manuel RSS yenileme tetikle
export async function forceRSSRefresh(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/rss/force-refresh`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to trigger RSS refresh");
  }
  return res.json();
}

// Fallback haberleri yeniden analiz et
export async function reAnalyzeFallbackNews(
  hours: number = 48
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/rss/re-analyze?hours=${hours}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to re-analyze news");
  }
  return res.json();
}

// Haber önceliğine göre renk belirle
export function getUrgencyColor(urgency: string): string {
  switch (urgency) {
    case "breaking":
      return "bg-red-500 text-white";
    case "high":
      return "bg-orange-500 text-white";
    case "medium":
      return "bg-yellow-500 text-black";
    default:
      return "bg-slate-500 text-white";
  }
}

// Haber önceliği etiketi
export function getUrgencyLabel(urgency: string): string {
  switch (urgency) {
    case "breaking":
      return "🚨 Breaking";
    case "high":
      return "🔴 Yüksek";
    case "medium":
      return "🟡 Orta";
    default:
      return "🟢 Düşük";
  }
}

// Etki yönüne göre renk
export function getImpactColor(direction: string): string {
  switch (direction) {
    case "bullish":
      return "text-green-400";
    case "bearish":
      return "text-red-400";
    default:
      return "text-gray-400";
  }
}

// Sembol için emoji
export function getSymbolEmoji(symbol: string): string {
  const emojis: Record<string, string> = {
    XAUUSD: "🥇",
    GOLD: "🥇",
    NDX: "📈",
    NASDAQ: "📈",
    DAX: "🏛️",
    USOIL: "🛢️",
    OIL: "🛢️",
    VIX: "⚠️",
    DXY: "💵",
    USD: "💵",
    EUR: "💶",
    GBP: "💷",
    JPY: "💴",
  };
  return emojis[symbol] || "📊";
}
