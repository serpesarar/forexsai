"use client";

import { useState, useEffect } from "react";
import {
  Brain,
  RefreshCw,
  AlertTriangle,
  ShieldAlert,
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Newspaper,
  Globe,
  Activity,
  Clock,
  ExternalLink,
  Filter,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useDetailedAIAnalysis } from "../lib/api/detailedAiAnalysis";
import { useI18nStore } from "../lib/i18n/store";
import { useClaudeAnalysisStore } from "../lib/claudeAnalysisStore";
import { useQuery } from "@tanstack/react-query";
import { fetchRSSNews, RSSNewsItem, getSymbolEmoji, getImpactColor } from "../lib/api/rssNews";

type Props = {
  symbol: string;
  symbolLabel: string;
};

function DecisionBadge({ decision, t }: { decision: string; t: (key: string) => string }) {
  const config =
    {
      BUY: { bg: "bg-success/20", text: "text-success", icon: TrendingUp, label: t("directions.buy") },
      SELL: { bg: "bg-danger/20", text: "text-danger", icon: TrendingDown, label: t("directions.sell") },
      HOLD: { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, label: t("directions.hold") },
    }[decision] || { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, label: decision };

  const Icon = config.icon;
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}>
      <Icon className={`w-4 h-4 ${config.text}`} />
      <span className={`text-sm font-semibold ${config.text}`}>{config.label}</span>
    </div>
  );
}

function fmtNum(v: any, digits = 2) {
  const n = typeof v === "number" ? v : v == null ? null : Number(v);
  if (n == null || Number.isNaN(n)) return "-";
  return n.toLocaleString("tr-TR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtPct(v: any, digits = 2) {
  const n = typeof v === "number" ? v : v == null ? null : Number(v);
  if (n == null || Number.isNaN(n)) return "-";
  return `${n.toFixed(digits)}%`;
}

function mlLabel(direction: string, t: (key: string) => string) {
  if (!direction) return "-";
  const d = String(direction).toUpperCase();
  if (d === "BUY") return t("directions.buy");
  if (d === "SELL") return t("directions.sell");
  if (d === "HOLD") return t("directions.hold");
  return d;
}

// Haber etkisini normalize et
function normalizeSymbol(symbol: string): string {
  const map: Record<string, string> = {
    "NDX.INDX": "NDX",
    "XAUUSD": "XAUUSD",
    "GDAXI.INDX": "DAX",
    "USOIL.FOREX": "USOIL",
    "DXY.INDX": "DXY",
    "VIX.INDX": "VIX",
  };
  return map[symbol] || symbol.replace(".INDX", "").replace(".FOREX", "");
}

export default function DetailedAnalysisPanel({ symbol, symbolLabel }: Props) {
  const { t, locale } = useI18nStore();
  const { data: fetchedData, isLoading, isFetching, error, refetch } = useDetailedAIAnalysis(symbol);
  const [showContext, setShowContext] = useState(false);
  const [showNews, setShowNews] = useState(true);
  const [newsFilter, setNewsFilter] = useState<"all" | "high" | "breaking">("all");
  const { getDetailed, setDetailed, getLastUpdated } = useClaudeAnalysisStore();
  
  // Get persisted data
  const persistedData = getDetailed(symbol);
  const lastUpdated = getLastUpdated(symbol);
  
  // Use fetched data if available, otherwise use persisted data
  const data = fetchedData || persistedData;
  
  // Persist new data when fetched
  useEffect(() => {
    if (fetchedData) {
      setDetailed(symbol, fetchedData);
    }
  }, [fetchedData, symbol, setDetailed]);

  // Fetch related news for this symbol
  const normalizedSymbol = normalizeSymbol(symbol);
  const { data: relatedNews, isLoading: newsLoading } = useQuery({
    queryKey: ["detailed-news", normalizedSymbol],
    queryFn: () => fetchRSSNews(48, 30, normalizedSymbol),
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
  });

  // Filter news
  const filteredNews = relatedNews?.filter((news) => {
    if (newsFilter === "high") return news.urgency === "high" || news.urgency === "breaking";
    if (newsFilter === "breaking") return news.urgency === "breaking";
    return true;
  });

  // Calculate sentiment from news
  const newsSentiment = useNewsSentimentAnalysis(filteredNews || [], normalizedSymbol);

  const analysis = (data?.analysis || {}) as any;
  const context = (data?.context || {}) as any;
  const ml = (context?.ml_prediction || {}) as any;

  const decision = analysis.final_decision || "HOLD";
  const confidence = analysis.confidence;

  const keyLevels = analysis.key_levels || context?.levels || {};
  const marketRegime = analysis.market_regime || {};
  const macroView = analysis.macro_view || context?.macro || {};
  const newsImpact = analysis.news_impact || context?.news || {};
  const rm = analysis.risk_management || {};
  
  // Fallback to context data if analysis is missing values
  const contextMacro = context?.macro || {};
  const contextVolatility = context?.volatility || {};
  const contextLevels = context?.levels || {};
  const contextDistances = context?.distances || {};
  const redFlags = Array.isArray(analysis.red_flags) ? analysis.red_flags : [];
  
  // Thesis can be an object with bull_case/bear_case or an array
  const thesisObj = analysis.thesis || {};
  const thesisSummary = typeof thesisObj === 'object' && !Array.isArray(thesisObj) ? thesisObj.summary : null;
  const bullCase = Array.isArray(thesisObj.bull_case) ? thesisObj.bull_case : [];
  const bearCase = Array.isArray(thesisObj.bear_case) ? thesisObj.bear_case : [];
  const whyDecision = typeof thesisObj === 'object' ? thesisObj.why_this_decision : null;
  // Legacy support: if thesis is an array, use it directly
  const thesisArray = Array.isArray(thesisObj) ? thesisObj : [];

  const emaD = keyLevels.ema_distances_pct || {};
  const ns = keyLevels.nearest_support || contextLevels.nearest_support || {};
  const nr = keyLevels.nearest_resistance || contextLevels.nearest_resistance || {};
  
  // EMA distances fallback from context
  const ema20Dist = emaD.ema20 ?? emaD.ema_20 ?? contextDistances.ema20_pct;
  const ema50Dist = emaD.ema50 ?? emaD.ema_50 ?? contextDistances.ema50_pct;
  const ema200Dist = emaD.ema200 ?? emaD.ema_200 ?? contextDistances.ema200_pct;
  
  // Market regime with fallback
  const trend = marketRegime.trend || contextVolatility.level ? (contextVolatility.level === "HIGH" ? "VOLATILE" : "NORMAL") : "UNKNOWN";
  const volatility = marketRegime.volatility || contextVolatility.level || "UNKNOWN";
  
  // Volume data from context
  const volumeData = context?.volume || {};
  const volumeStatus = volumeData.status || marketRegime.volume_confirmation || marketRegime.liquidity || "UNKNOWN";
  const volumeRatio = volumeData.ratio;
  const volumeLast = volumeData.last;
  const volumeAvg20 = volumeData.avg20;
  
  // Volume analysis helper
  const getVolumeWarning = () => {
    if (!volumeRatio || volumeStatus === "UNKNOWN") return null;
    
    const priceDirection = ml.direction === "BUY" ? "up" : ml.direction === "SELL" ? "down" : null;
    
    if (volumeRatio < 0.6 && priceDirection) {
      return {
        type: "warning",
        message: `⚠️ Düşük hacimle fiyat hareketi - ${priceDirection === "up" ? "Yükseliş" : "Düşüş"} güvenilir olmayabilir`,
        color: "text-amber-400"
      };
    }
    if (volumeRatio < 0.8 && priceDirection) {
      return {
        type: "caution",
        message: `Hacim ortalamanın altında (${(volumeRatio * 100).toFixed(0)}%) - Dikkatli olun`,
        color: "text-amber-300"
      };
    }
    if (volumeRatio > 1.5) {
      return {
        type: "strong",
        message: `✓ Güçlü hacim teyidi (${(volumeRatio * 100).toFixed(0)}%) - Hareket destekleniyor`,
        color: "text-success"
      };
    }
    if (volumeRatio > 1.2) {
      return {
        type: "good",
        message: `Hacim ortalamanın üzerinde - İşlem güvenli`,
        color: "text-emerald-400"
      };
    }
    return null;
  };
  
  const volumeWarning = getVolumeWarning();

  // Backend field mapping (Claude returns different names)
  const rmEntry = rm.recommended_entry ?? rm.entry;
  const rmTp = rm.recommended_tp ?? rm.take_profit;
  const rmSl = rm.recommended_sl ?? rm.stop_loss;
  const rmInvalidation = rm.invalidation ?? rm.size_rationale;

  return (
    <div className="glass-premium p-8 space-y-6 rounded-2xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/30 to-sky-500/30">
            <Brain className="h-6 w-6 text-sky-400" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("detailedAnalysis.title")}</p>
            <h3 className="text-xl font-bold">{symbolLabel}</h3>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="p-3 rounded-xl hover:bg-white/10 transition"
            disabled={isFetching}
          >
            <RefreshCw className={`w-5 h-5 ${isFetching ? "animate-spin text-sky-400" : "text-textSecondary"}`} />
          </button>
        </div>
      </div>

      {/* Show last updated time if we have persisted data */}
      {lastUpdated && data && !isLoading && (
        <div className="flex items-center gap-2 text-xs text-textSecondary bg-white/5 px-3 py-2 rounded-lg">
          <Clock className="w-3 h-3" />
          <span>{t("claudeAnalysis.lastAnalysis")}: {new Date(lastUpdated).toLocaleString(locale === "en" ? "en-US" : "tr-TR")}</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-12 w-full rounded-xl" />
          <div className="skeleton h-24 w-full rounded-xl" />
          <div className="skeleton h-28 w-full rounded-xl" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 bg-danger/10 rounded-xl text-danger">
          <AlertTriangle className="w-5 h-5" />
          <span className="text-sm">{t("detailedAnalysis.error")}</span>
        </div>
      ) : data ? (
        <>
          {/* Decision Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white/5 rounded-2xl p-5 border border-white/5">
            <div className="flex flex-wrap items-center gap-3">
              <DecisionBadge decision={decision} t={t} />
              <div className="text-sm text-textSecondary">
                <span className="font-medium">{t("detailedAnalysis.claudeConfidence")}:</span> {typeof confidence === "number" ? `${confidence.toFixed(0)}%` : "-"}
              </div>

              <div className="hidden sm:block h-6 w-px bg-white/10" />

              <div className="text-sm text-textSecondary">
                <span className="font-medium">ML:</span> {mlLabel(ml.direction, t)}
                <span className="text-textSecondary"> · </span>
                <span className="font-medium">{t("detailedAnalysis.mlConfidence")}:</span> {typeof ml.confidence === "number" ? `${Number(ml.confidence).toFixed(0)}%` : "-"}
              </div>
            </div>
            <div className="text-xs text-textSecondary">
              {analysis.model_used ? String(analysis.model_used) : ""}
            </div>
          </div>

          {analysis.summary && (
            <div className="bg-white/5 rounded-2xl p-5 border border-white/5 text-sm text-textSecondary leading-relaxed">
              {String(analysis.summary)}
            </div>
          )}

          {/* NEWS SECTION - NEW */}
          {showNews && (
            <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-2xl p-5 border border-purple-500/20">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Newspaper className="w-4 h-4 text-purple-400" />
                  <p className="text-xs font-semibold uppercase tracking-wider text-purple-300">
                    AI-Analizli İlgili Haberler ({filteredNews?.length || 0})
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={newsFilter}
                    onChange={(e) => setNewsFilter(e.target.value as any)}
                    className="bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-300"
                  >
                    <option value="all">Tümü</option>
                    <option value="high">Yüksek Etki</option>
                    <option value="breaking">Breaking</option>
                  </select>
                  <button
                    onClick={() => setShowNews(false)}
                    className="p-1 hover:bg-white/10 rounded transition"
                  >
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              </div>

              {newsLoading ? (
                <div className="flex items-center justify-center py-4">
                  <div className="animate-spin w-5 h-5 border-2 border-purple-500/30 border-t-purple-500 rounded-full" />
                </div>
              ) : filteredNews && filteredNews.length > 0 ? (
                <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                  {filteredNews.slice(0, 5).map((news) => (
                    <NewsItem key={news.id} news={news} symbol={normalizedSymbol} />
                  ))}
                  {filteredNews.length > 5 && (
                    <p className="text-xs text-slate-400 text-center py-2">
                      +{filteredNews.length - 5} daha fazla haber
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-sm text-slate-400 text-center py-4">
                  Son 48 saatte ilgili haber bulunamadı
                </p>
              )}

              {/* News Sentiment Summary */}
              {newsSentiment && (
                <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-3 gap-3">
                  <div className="text-center">
                    <p className="text-[10px] text-slate-400">Haber Etkisi</p>
                    <p className={`text-sm font-semibold ${getImpactColor(newsSentiment.overallDirection)}`}>
                      {newsSentiment.overallDirection === "bullish" ? "🟢 Pozitif" : 
                       newsSentiment.overallDirection === "bearish" ? "🔴 Negatif" : "⚪ Nötr"}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] text-slate-400">Ortalama Skor</p>
                    <p className="text-sm font-semibold text-slate-200">
                      {newsSentiment.avgScore.toFixed(1)}/10
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] text-slate-400">Güven</p>
                    <p className="text-sm font-semibold text-slate-200">
                      {newsSentiment.avgConfidence.toFixed(0)}%
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {!showNews && (
            <button
              onClick={() => setShowNews(true)}
              className="w-full flex items-center justify-center gap-2 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-sm text-slate-400 transition"
            >
              <Newspaper className="w-4 h-4" />
              Haber Analizini Göster
              <ChevronDown className="w-4 h-4" />
            </button>
          )}

          {/* Key Levels & Market Regime */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-accent" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">{t("detailedAnalysis.levelsDistances")}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">{t("detailedAnalysis.nearestSupport")}</p>
                  <p className="font-mono font-semibold">{fmtNum(ns.price, 2)}</p>
                  <p className="text-[11px] text-textSecondary">{t("detailedAnalysis.distance")}: {fmtPct(ns.distance_pct, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">{t("detailedAnalysis.nearestResistance")}</p>
                  <p className="font-mono font-semibold">{fmtNum(nr.price, 2)}</p>
                  <p className="text-[11px] text-textSecondary">{t("detailedAnalysis.distance")}: {fmtPct(nr.distance_pct, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">EMA20 {t("detailedAnalysis.distance")}</p>
                  <p className="font-mono font-semibold">{fmtPct(ema20Dist, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">EMA50 / EMA200</p>
                  <p className="font-mono font-semibold">{fmtPct(ema50Dist, 2)} / {fmtPct(ema200Dist, 2)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-cyan-400" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">{t("detailedAnalysis.marketRegime")}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">Trend</p>
                  <p className="font-semibold">{trend !== "UNKNOWN" ? String(trend) : (context?.market_structure?.structure || "-")}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">Volatilite</p>
                  <p className="font-semibold">{volatility !== "UNKNOWN" ? String(volatility) : "-"}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">{t("detailedAnalysis.volumeConfirmation")}</p>
                  <p className={`font-semibold ${volumeStatus === "STRONG" ? "text-success" : volumeStatus === "WEAK" ? "text-amber-400" : ""}`}>
                    {volumeStatus !== "UNKNOWN" ? volumeStatus : "-"}
                  </p>
                  {volumeRatio && (
                    <p className="text-[10px] text-textSecondary mt-1">
                      {t("detailedAnalysis.ratio")}: {(volumeRatio * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">{t("detailedAnalysis.lastAvg")}</p>
                  <p className="font-mono text-xs">
                    {volumeLast ? fmtNum(volumeLast, 0) : "-"} / {volumeAvg20 ? fmtNum(volumeAvg20, 0) : "-"}
                  </p>
                </div>
              </div>
              {volumeWarning && (
                <div className={`mt-3 p-3 rounded-xl bg-white/5 border border-white/5 text-xs ${volumeWarning.color}`}>
                  {volumeWarning.message}
                </div>
              )}
            </div>
          </div>

          {/* Macro & News Impact */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-emerald-400" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">{t("detailedAnalysis.macroProxy")}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">DXY</p>
                  <p className="font-mono font-semibold">{fmtNum(macroView.dxy?.price ?? contextMacro.dxy?.price, 2)}</p>
                  {(macroView.dxy?.impact || contextMacro.dxy?.impact) && <p className="text-[10px] text-textSecondary">{macroView.dxy?.impact || contextMacro.dxy?.impact}</p>}
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">VIX</p>
                  <p className="font-mono font-semibold">{fmtNum(macroView.vix?.price ?? contextMacro.vix?.price ?? contextVolatility.vix, 2)}</p>
                  {(macroView.vix?.impact || contextMacro.vix?.impact) && <p className="text-[10px] text-textSecondary">{macroView.vix?.impact || contextMacro.vix?.impact}</p>}
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Newspaper className="w-4 h-4 text-amber-400" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">{t("detailedAnalysis.newsImpact")}</p>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="text-textSecondary">{t("detailedAnalysis.headlineCount")}</div>
                <div className="font-mono font-semibold">{typeof newsImpact.headline_count === "number" ? newsImpact.headline_count : (newsImpact.count ?? filteredNews?.length ?? "-")}</div>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <div className="text-textSecondary">Tone</div>
                <div className="font-semibold">{newsSentiment?.overallDirection || newsImpact.tone || "-"}</div>
              </div>
              {Array.isArray(newsImpact.headlines) && newsImpact.headlines.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {newsImpact.headlines.slice(0, 3).map((h: any, i: number) => (
                    <li key={i} className="text-xs text-textSecondary truncate">
                      {typeof h === "string" ? h : h?.title || String(h)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Risk Management */}
          <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-accent" />
              <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">{t("detailedAnalysis.riskManagement")}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-textSecondary">Entry</p>
                <p className="font-mono font-semibold">{fmtNum(rmEntry, 2)}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-success">TP</p>
                <p className="font-mono font-semibold text-success">{fmtNum(rmTp, 2)}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-danger">SL</p>
                <p className="font-mono font-semibold text-danger">{fmtNum(rmSl, 2)}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-textSecondary">{t("detailedAnalysis.size")}</p>
                <p className="font-semibold">{rm.position_size ? String(rm.position_size) : "-"}</p>
              </div>
            </div>
            {rmInvalidation && (
              <div className="mt-3 text-xs text-textSecondary leading-relaxed">
                <span className="font-semibold">Invalidation:</span> {String(rmInvalidation)}
              </div>
            )}
          </div>

          {/* Thesis Section */}
          {(bullCase.length > 0 || bearCase.length > 0 || thesisArray.length > 0 || redFlags.length > 0 || thesisSummary) && (
            <div className="space-y-4">
              {/* Thesis Summary */}
              {thesisSummary && (
                <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
                  <div className="flex items-center gap-2 mb-3">
                    <ShieldAlert className="w-4 h-4 text-accent" />
                    <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">{t("detailedAnalysis.thesisSummary")}</p>
                  </div>
                  <p className="text-sm text-textSecondary leading-relaxed">{String(thesisSummary)}</p>
                  {whyDecision && (
                    <p className="text-xs text-textSecondary mt-2 pt-2 border-t border-white/10">
                      <span className="font-semibold">{t("detailedAnalysis.decisionReason")}:</span> {String(whyDecision)}
                    </p>
                  )}
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Bull Case (Positive Thesis) */}
                <div className="bg-success/5 rounded-2xl p-5 border border-success/10">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="w-4 h-4 text-success" />
                    <p className="text-xs font-semibold uppercase tracking-wider text-success">{t("detailedAnalysis.bullThesis")}</p>
                  </div>
                  <ul className="space-y-1">
                    {bullCase.length > 0 ? (
                      bullCase.slice(0, 6).map((t: any, i: number) => (
                        <li key={i} className="text-xs text-textSecondary">• {String(t)}</li>
                      ))
                    ) : thesisArray.length > 0 ? (
                      thesisArray.slice(0, 6).map((t: any, i: number) => (
                        <li key={i} className="text-xs text-textSecondary">• {String(t)}</li>
                      ))
                    ) : (
                      <li className="text-xs text-textSecondary/50">{t("detailedAnalysis.noData")}</li>
                    )}
                  </ul>
                </div>

                {/* Bear Case / Red Flags */}
                <div className="bg-danger/5 rounded-2xl p-5 border border-danger/10">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingDown className="w-4 h-4 text-danger" />
                    <p className="text-xs font-semibold uppercase tracking-wider text-danger">{t("detailedAnalysis.bearThesis")}</p>
                  </div>
                  <ul className="space-y-1">
                    {bearCase.length > 0 ? (
                      bearCase.slice(0, 6).map((r: any, i: number) => (
                        <li key={i} className="text-xs text-textSecondary">• {String(r)}</li>
                      ))
                    ) : redFlags.length > 0 ? (
                      redFlags.slice(0, 6).map((r: any, i: number) => (
                        <li key={i} className="text-xs text-textSecondary">• {String(r)}</li>
                      ))
                    ) : (
                      <li className="text-xs text-textSecondary/50">{t("detailedAnalysis.noData")}</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-[10px] text-textSecondary pt-2 border-t border-white/5">
            <button
              onClick={() => setShowContext(!showContext)}
              className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition text-xs"
            >
              {showContext ? t("detailedAnalysis.hideContext") : t("detailedAnalysis.showContext")}
            </button>
            <span>
              {analysis.timestamp ? new Date(String(analysis.timestamp)).toLocaleTimeString(locale === "en" ? "en-US" : "tr-TR") : ""}
            </span>
          </div>

          {showContext && (
            <div className="p-3 bg-white/5 rounded-xl text-xs text-textSecondary leading-relaxed max-h-64 overflow-auto">
              <pre className="whitespace-pre-wrap break-words">{JSON.stringify(context, null, 2)}</pre>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

// News Item Component
function NewsItem({ news, symbol }: { news: RSSNewsItem; symbol: string }) {
  const getUrgencyIcon = (urgency: string) => {
    if (urgency === "breaking") return "🚨";
    if (urgency === "high") return "🔴";
    if (urgency === "medium") return "🟡";
    return "🟢";
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffMins < 5) return "Şimdi";
    if (diffMins < 60) return `${diffMins}d`;
    if (diffHours < 24) return `${diffHours}s`;
    return `${Math.floor(diffHours / 24)}g`;
  };

  // Find symbol-specific impact
  const symbolImpact = news.impacts?.find(
    (i) => i.symbol === symbol || i.symbol === symbol.replace(".INDX", "")
  );

  return (
    <div className="bg-white/5 rounded-xl p-3 border border-white/10 hover:bg-white/10 transition">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm">{getUrgencyIcon(news.urgency)}</span>
            <span className="text-[10px] text-slate-400">{news.source}</span>
            <span className="text-[10px] text-slate-500">{formatTime(news.timestamp)}</span>
          </div>
          <p className="text-xs font-medium text-slate-200 line-clamp-2">
            {news.headline_tr || news.headline}
          </p>
          {symbolImpact && (
            <div className="flex items-center gap-2 mt-1">
              <span className={getImpactColor(symbolImpact.direction)}>
                {symbolImpact.direction === "bullish" ? "🟢" : symbolImpact.direction === "bearish" ? "🔴" : "⚪"}
                {" "}{symbolImpact.score}/10
              </span>
              {symbolImpact.reasoning_tr && (
                <span className="text-[10px] text-slate-400 truncate">{symbolImpact.reasoning_tr}</span>
              )}
            </div>
          )}
        </div>
        {news.url && (
          <a
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:bg-white/10 rounded transition flex-shrink-0"
          >
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
        )}
      </div>
    </div>
  );
}

// Hook: News Sentiment Analysis
function useNewsSentimentAnalysis(news: RSSNewsItem[], symbol: string) {
  return useMemo(() => {
    if (!news || news.length === 0) return null;

    const symbolImpacts = news
      .flatMap((n) => n.impacts || [])
      .filter((i) => i.symbol === symbol || i.symbol === symbol.replace(".INDX", ""));

    if (symbolImpacts.length === 0) return null;

    const bullishCount = symbolImpacts.filter((i) => i.direction === "bullish").length;
    const bearishCount = symbolImpacts.filter((i) => i.direction === "bearish").length;
    const neutralCount = symbolImpacts.filter((i) => i.direction === "neutral").length;

    const totalScore = symbolImpacts.reduce((sum, i) => sum + i.score, 0);
    const totalConfidence = symbolImpacts.reduce((sum, i) => sum + i.confidence, 0);

    let overallDirection: "bullish" | "bearish" | "neutral" = "neutral";
    if (bullishCount > bearishCount && bullishCount > neutralCount) overallDirection = "bullish";
    else if (bearishCount > bullishCount && bearishCount > neutralCount) overallDirection = "bearish";

    return {
      overallDirection,
      bullishCount,
      bearishCount,
      neutralCount,
      avgScore: totalScore / symbolImpacts.length,
      avgConfidence: (totalConfidence / symbolImpacts.length) * 100,
      totalImpacts: symbolImpacts.length,
    };
  }, [news, symbol]);
}

// useMemo import for the hook
import { useMemo } from "react";
