"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Brain,
  Newspaper,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Clock,
  RefreshCw,
  Sparkles,
  Target,
  Shield,
  Zap,
  Crown,
  Lock,
} from "lucide-react";
import { useI18n } from "@/lib/i18n/store";
import { useIsPro, useIsAuthenticated } from "@/lib/auth/store";

interface NewsAnalysisItem {
  headline: string;
  sentiment: number;
  confidence: number;
  category: string;
  time_sensitivity: string;
  key_entities: string[];
  rationale: string;
  override_signal: string | null;
}

interface ClaudeAnalysisResponse {
  symbol: string;
  timestamp: string;
  news_count: number;
  analyzed_count: number;
  overall_sentiment: number;
  overall_confidence: number;
  direction_bias: string;
  analyses: NewsAnalysisItem[];
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  has_override: boolean;
  override_signal: string | null;
  override_reason: string | null;
  categories: Record<string, number>;
  tokens_used: number;
  estimated_cost_usd: number;
  market_commentary: string;
  key_risks: string[];
  key_opportunities: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ClaudeNewsAnalysisPanel() {
  const { t } = useI18n();
  const isPro = useIsPro();
  const isAuthenticated = useIsAuthenticated();
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<"XAUUSD" | "NDX.INDX">("XAUUSD");
  const [analysis, setAnalysis] = useState<ClaudeAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshNews = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/claude-news/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: selectedSymbol, limit: 30 }),
      });
      if (!res.ok) throw new Error("Failed to refresh news");
      const data = await res.json();
      console.log("News refreshed:", data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setRefreshing(false);
    }
  };

  const analyzeNews = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/claude-news/analyze/${selectedSymbol}?limit=15&hours_back=24`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error("Failed to analyze news");
      const data: ClaudeAnalysisResponse = await res.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.3) return "text-green-500";
    if (sentiment < -0.3) return "text-red-500";
    return "text-yellow-500";
  };

  const getSentimentBg = (sentiment: number) => {
    if (sentiment > 0.3) return "bg-green-500/10 border-green-500/30";
    if (sentiment < -0.3) return "bg-red-500/10 border-red-500/30";
    return "bg-yellow-500/10 border-yellow-500/30";
  };

  const getDirectionIcon = (direction: string) => {
    if (direction === "BUY") return <TrendingUp className="h-5 w-5 text-green-500" />;
    if (direction === "SELL") return <TrendingDown className="h-5 w-5 text-red-500" />;
    return <Minus className="h-5 w-5 text-yellow-500" />;
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "geopolitical": return "🌍";
      case "monetary": return "🏦";
      case "economic": return "📊";
      case "technical": return "📈";
      case "commodity_specific": return "🥇";
      default: return "📰";
    }
  };

  const getTimeSensitivityBadge = (sensitivity: string) => {
    const colors: Record<string, string> = {
      immediate: "bg-red-500",
      short_term: "bg-orange-500",
      medium_term: "bg-blue-500",
      long_term: "bg-gray-500",
    };
    return colors[sensitivity] || "bg-gray-500";
  };

  return (
    <Card className="bg-slate-900/50 border-slate-700">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Brain className="h-5 w-5 text-purple-400" />
            Claude AI Haber Analizi
          </CardTitle>
          <div className="flex items-center gap-2">
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value as "XAUUSD" | "NDX.INDX")}
              className="bg-slate-800 border-slate-600 rounded-md px-3 py-1.5 text-sm"
            >
              <option value="XAUUSD">🥇 XAUUSD</option>
              <option value="NDX.INDX">📈 NASDAQ</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Pro Requirement Banner - shown for non-pro users */}
        {!isPro && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-purple-900/50 to-pink-900/50 border border-purple-500/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center shrink-0">
                <Crown className="w-5 h-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="text-purple-200 font-medium">Pro Üyelik Gerekli</p>
                <p className="text-sm text-slate-400">
                  Claude AI analizi sadece Pro üyeler için kullanılabilir.
                </p>
              </div>
              <a
                href={isAuthenticated ? "/upgrade" : "/signup"}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-sm font-medium transition-all shrink-0"
              >
                {isAuthenticated ? "Pro'ya Geç" : "Ücretsiz Kayıt"}
              </a>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={refreshNews}
            disabled={refreshing}
            variant="outline"
            size="sm"
            className="flex-1"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Yenileniyor..." : "Haberleri Yenile"}
          </Button>
          <Button
            onClick={analyzeNews}
            disabled={loading || !isPro}
            className={`flex-1 ${isPro ? "bg-purple-600 hover:bg-purple-700" : "bg-slate-700 cursor-not-allowed"}`}
            size="sm"
          >
            {isPro ? (
              <>
                <Sparkles className={`h-4 w-4 mr-2 ${loading ? "animate-pulse" : ""}`} />
                {loading ? "Analiz Ediliyor..." : "Claude ile Analiz Et"}
              </>
            ) : (
              <>
                <Lock className="h-4 w-4 mr-2" />
                Pro Üyelik Gerekli
              </>
            )}
          </Button>
        </div>

        {/* Cost Warning - only show for pro users */}
        {isPro && (
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <DollarSign className="h-3 w-3" />
            <span>Her analiz ~$0.01-0.05 API maliyeti oluşturur</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            <AlertTriangle className="h-4 w-4 inline mr-2" />
            {error}
          </div>
        )}

        {/* Analysis Result */}
        {analysis && (
          <div className="space-y-4">
            {/* Overall Summary */}
            <div className={`rounded-lg border p-4 ${getSentimentBg(analysis.overall_sentiment)}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  {getDirectionIcon(analysis.direction_bias)}
                  <div>
                    <div className="font-semibold text-lg">
                      {analysis.direction_bias === "BUY" ? "ALIŞ Yanlısı" : 
                       analysis.direction_bias === "SELL" ? "SATIŞ Yanlısı" : "NÖTR"}
                    </div>
                    <div className="text-sm text-slate-400">
                      {analysis.analyzed_count} / {analysis.news_count} haber analiz edildi
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold ${getSentimentColor(analysis.overall_sentiment)}`}>
                    {analysis.overall_sentiment > 0 ? "+" : ""}{(analysis.overall_sentiment * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-slate-400">
                    Güven: {analysis.overall_confidence.toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Sentiment Distribution */}
              <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span>{analysis.bullish_count} Bullish</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>{analysis.bearish_count} Bearish</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <span>{analysis.neutral_count} Nötr</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-3 flex gap-1 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-green-500 transition-all" 
                  style={{ width: `${(analysis.bullish_count / analysis.analyzed_count) * 100}%` }}
                />
                <div 
                  className="bg-yellow-500 transition-all" 
                  style={{ width: `${(analysis.neutral_count / analysis.analyzed_count) * 100}%` }}
                />
                <div 
                  className="bg-red-500 transition-all" 
                  style={{ width: `${(analysis.bearish_count / analysis.analyzed_count) * 100}%` }}
                />
              </div>
            </div>

            {/* Override Signal */}
            {analysis.has_override && (
              <div className={`rounded-lg border p-3 ${
                analysis.override_signal === "FORCE_BUY" 
                  ? "bg-green-500/20 border-green-500" 
                  : "bg-red-500/20 border-red-500"
              }`}>
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  <span className="font-bold">
                    {analysis.override_signal === "FORCE_BUY" ? "🚀 GÜÇLÜ AL SİNYALİ" : "⚠️ GÜÇLÜ SAT SİNYALİ"}
                  </span>
                </div>
                <div className="text-sm mt-1 opacity-80">{analysis.override_reason}</div>
              </div>
            )}

            {/* Market Commentary */}
            {analysis.market_commentary && (
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2 text-sm font-medium">
                  <Brain className="h-4 w-4 text-purple-400" />
                  Claude Piyasa Yorumu
                </div>
                <p className="text-sm text-slate-300">{analysis.market_commentary}</p>
              </div>
            )}

            {/* Risks & Opportunities */}
            <div className="grid grid-cols-2 gap-3">
              {analysis.key_risks.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2 text-sm font-medium text-red-400">
                    <Shield className="h-4 w-4" />
                    Riskler
                  </div>
                  <ul className="text-xs space-y-1 text-slate-300">
                    {analysis.key_risks.map((risk, i) => (
                      <li key={i}>• {risk}</li>
                    ))}
                  </ul>
                </div>
              )}
              {analysis.key_opportunities.length > 0 && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2 text-sm font-medium text-green-400">
                    <Target className="h-4 w-4" />
                    Fırsatlar
                  </div>
                  <ul className="text-xs space-y-1 text-slate-300">
                    {analysis.key_opportunities.map((opp, i) => (
                      <li key={i}>• {opp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Individual Analyses */}
            <div className="space-y-2">
              <div className="text-sm font-medium flex items-center gap-2">
                <Newspaper className="h-4 w-4" />
                Haber Detayları
              </div>
              <div className="max-h-64 overflow-y-auto space-y-2 pr-2">
                {analysis.analyses.map((item, i) => (
                  <div
                    key={i}
                    className={`rounded-lg border p-3 text-sm ${getSentimentBg(item.sentiment)}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span>{getCategoryIcon(item.category)}</span>
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${getTimeSensitivityBadge(item.time_sensitivity)} text-white`}
                          >
                            {item.time_sensitivity}
                          </Badge>
                          {item.override_signal && (
                            <Badge className="bg-purple-600 text-xs">
                              {item.override_signal}
                            </Badge>
                          )}
                        </div>
                        <p className="text-slate-200 line-clamp-2">{item.headline}</p>
                        <p className="text-xs text-slate-400 mt-1">{item.rationale}</p>
                        {item.key_entities.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {item.key_entities.map((entity, j) => (
                              <Badge key={j} variant="outline" className="text-xs">
                                {entity}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="text-right shrink-0">
                        <div className={`font-bold ${getSentimentColor(item.sentiment)}`}>
                          {item.sentiment > 0 ? "+" : ""}{(item.sentiment * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-slate-400">
                          {item.confidence}% güven
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cost & Meta */}
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-700">
              <div className="flex items-center gap-4">
                <span>📊 {analysis.tokens_used} token</span>
                <span>💰 ${analysis.estimated_cost_usd.toFixed(4)}</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(analysis.timestamp).toLocaleTimeString("tr-TR")}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!analysis && !loading && !error && (
          <div className="text-center py-8 text-slate-500">
            <Brain className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>Henüz analiz yapılmadı</p>
            <p className="text-sm mt-1">Önce haberleri yenileyin, sonra Claude ile analiz edin</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default ClaudeNewsAnalysisPanel;
