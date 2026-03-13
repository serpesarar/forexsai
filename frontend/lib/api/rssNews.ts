/**
 * RSS News API Client
 * DeepSeek AI analizli haberler için API çağrıları
 */

import { getApiBase } from "./base";

const API_BASE = getApiBase();

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
  summary_en?: string;
  summary_tr?: string;
  analysis_en?: string;
  analysis_tr?: string;
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

  const url = `${API_BASE}/api/rss/news?${params}`;
  console.log("[fetchRSSNews] Fetching:", url);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
    
    const res = await fetch(url, { 
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      }
    });
    clearTimeout(timeoutId);
    
    console.log("[fetchRSSNews] Response status:", res.status);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error("[fetchRSSNews] Error:", errorText);
      throw new Error(`Failed to fetch RSS news: ${res.status}`);
    }
    
    const data = await res.json();
    console.log("[fetchRSSNews] Data count:", data?.length);
    return data;
  } catch (error) {
    console.error("[fetchRSSNews] Fetch error:", error);
    throw error;
  }
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

// Ekonomik takvim verilerini getir (ekonomik olaylar + kazançlar)
export async function fetchEconomicCalendar(
  date?: string,
  currency?: string
): Promise<any[]> {
  const params = new URLSearchParams();
  if (date) params.append("date", date);
  if (currency) params.append("currency", currency);

  // Fetch both economic events and earnings
  const [economicRes, earningsRes] = await Promise.all([
    fetch(`${API_BASE}/api/calendar/economic?${params}`),
    fetch(`${API_BASE}/api/calendar/earnings?${params}`)
  ]);

  if (!economicRes.ok) {
    console.error("[fetchEconomicCalendar] Economic fetch failed:", await economicRes.text());
    throw new Error("Failed to fetch economic calendar");
  }

  const economicData = await economicRes.json();
  const economicEvents = (economicData.events || []).map((e: any) => ({...e, is_earnings: false}));

  let earningsEvents: any[] = [];
  if (earningsRes.ok) {
    const earningsData = await earningsRes.json();
    earningsEvents = (earningsData.earnings || []).map((e: any) => ({
      ...e,
      is_earnings: true,
      event_name: e.title || `${e.company} Earnings`,
      currency: "USD",
      impact: e.impact || "High"
    }));
  } else {
    console.warn("[fetchEconomicCalendar] Earnings fetch failed (non-critical)");
  }

  // Combine and sort by timestamp
  const allEvents = [...economicEvents, ...earningsEvents];
  allEvents.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  console.log(`[fetchEconomicCalendar] Fetched ${economicEvents.length} economic + ${earningsEvents.length} earnings events`);
  return allEvents;
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

// Interface for candle news response
export interface CandleNewsResponse {
  success: boolean;
  symbol: string;
  candle: {
    timestamp: string;
    change_pct: number;
    range_pct: number;
    is_significant: boolean;
  };
  news_count: number;
  news: MatchedNewsItem[];
}

interface LegacyCandleNewsResponse {
  success: boolean;
  data?: {
    symbol?: string;
    candle_time?: string;
    timeframe?: string;
    news_count?: number;
    news?: MatchedNewsItem[];
  };
}

export interface MatchedNewsItem {
  id: string;
  headline: string;
  headline_en: string;
  summary_en?: string;
  summary_tr?: string;
  analysis_en?: string;
  analysis_tr?: string;
  headline_locale?: string;
  summary_locale?: string;
  analysis_locale?: string;
  timestamp: string;
  source: string;
  catalyst_type?: "news" | "economic" | "earnings";
  match_quality?: "matched" | "context";
  urgency: string;
  score: number;
  direction: string;
  reasoning?: string;
  reasoning_tr: string;
  reasoning_locale?: string;
  event_id?: string;
  affected_symbols?: string[];
  relevance_score: number;
  importance_level?: string;
  importance_score?: number;
  importance_reason?: string;
  ai_model?: string;
  ai_match_confidence?: number;
  url: string;
}

// AKILLI HABER-MUM EŞLEŞTİRME
// Büyük mum hareketlerini gerçekten açıklayan haberleri getir
export async function fetchNewsForCandle(
  symbol: string,
  candleTimestamp: string,
  candleOpen: number,
  candleClose: number,
  candleHigh: number,
  candleLow: number,
  timeframe: string = "1h",
  locale?: string
): Promise<CandleNewsResponse> {
  const params = new URLSearchParams({
    candle_timestamp: candleTimestamp,
    candle_open: candleOpen.toString(),
    candle_close: candleClose.toString(),
    candle_high: candleHigh.toString(),
    candle_low: candleLow.toString(),
    timeframe: timeframe,
  });

  if (locale) {
    params.append("lang", locale);
  }

  const url = `${API_BASE}/api/rss/candle-news/${symbol}?${params}`;
  console.log("[fetchNewsForCandle] Fetching:", url);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const res = await fetch(url, {
      method: "POST",
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errorText = await res.text();
      console.error("[fetchNewsForCandle] Error:", errorText);
      throw new Error(`Failed to fetch candle news: ${res.status}`);
    }

    const data = await res.json() as CandleNewsResponse | LegacyCandleNewsResponse;
    const normalized: CandleNewsResponse = "news" in data
      ? data
      : {
          success: data.success,
          symbol: data.data?.symbol || symbol,
          candle: {
            timestamp: data.data?.candle_time || candleTimestamp,
            change_pct: 0,
            range_pct: 0,
            is_significant: false,
          },
          news_count: data.data?.news_count || 0,
          news: data.data?.news || [],
        };

    console.log(`[fetchNewsForCandle] Found ${normalized.news.length || 0} relevant news items`);
    return normalized;
  } catch (error) {
    console.error("[fetchNewsForCandle] Fetch error:", error);
    throw error;
  }
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
