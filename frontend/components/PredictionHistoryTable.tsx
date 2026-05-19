"use client";

import { useState } from "react";
import {
  History,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  XCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Filter,
} from "lucide-react";
import { usePredictionHistory, PredictionHistoryItem, fixMlCorrectInDatabase } from "../lib/api/learning";
import { useI18nStore } from "../lib/i18n/store";

interface PredictionHistoryTableProps {
  symbol?: string;
}

function DirectionBadge({ direction }: { direction: string }) {
  const config = {
    BUY: { bg: "bg-success/20", text: "text-success", icon: TrendingUp },
    SELL: { bg: "bg-danger/20", text: "text-danger", icon: TrendingDown },
    HOLD: { bg: "bg-white/10", text: "text-textSecondary", icon: Minus },
    UP: { bg: "bg-success/20", text: "text-success", icon: TrendingUp },
    DOWN: { bg: "bg-danger/20", text: "text-danger", icon: TrendingDown },
    FLAT: { bg: "bg-white/10", text: "text-textSecondary", icon: Minus },
  }[direction] || { bg: "bg-white/10", text: "text-textSecondary", icon: Minus };

  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <Icon className="w-3 h-3" />
      {direction}
    </span>
  );
}

function ResultBadge({ correct, hitTarget, hitStop, pending, direction }: { correct?: boolean; hitTarget?: boolean; hitStop?: boolean; pending?: boolean; direction?: string }) {
  if (pending) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400">
        <Clock className="w-3 h-3" />
        Pending
      </span>
    );
  }

  // HOLD signals are neutral — not directional, don't count as wrong
  if (direction === "HOLD") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-white/10 text-textSecondary">
        <Minus className="w-3 h-3" />
        Neutral
      </span>
    );
  }

  if (hitStop) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-danger/20 text-danger">
        <XCircle className="w-3 h-3" />
        Stop Hit
      </span>
    );
  }

  if (hitTarget) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-success/20 text-success">
        <Target className="w-3 h-3" />
        Target Hit
      </span>
    );
  }

  if (correct === true) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-success/20 text-success">
        <CheckCircle className="w-3 h-3" />
        Correct
      </span>
    );
  }

  if (correct === false) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-danger/20 text-danger">
        <XCircle className="w-3 h-3" />
        Wrong
      </span>
    );
  }

  return null;
}

function formatDate(dateStr: string, locale: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(locale === "en" ? "en-US" : "tr-TR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatPrice(price: number | undefined, symbol: string): string {
  if (price === undefined || price === null) return "-";
  // XAUUSD has 2 decimals, NDX has 2 decimals
  return price.toFixed(2);
}

export default function PredictionHistoryTable({ symbol }: PredictionHistoryTableProps) {
  const [days, setDays] = useState(7);
  const [limit, setLimit] = useState(30);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [filterResult, setFilterResult] = useState<"all" | "correct" | "wrong" | "pending">("all");
  const [isFixing, setIsFixing] = useState(false);
  
  const { data, isLoading, error, refetch } = usePredictionHistory(symbol, days, limit);
  const t = useI18nStore((s) => s.t);
  const locale = useI18nStore((s) => s.locale);

  // Fix database ml_correct values
  const handleFixDatabase = async () => {
    setIsFixing(true);
    try {
      await fixMlCorrectInDatabase();
      refetch();
    } catch (e) {
      console.error("Failed to fix database:", e);
    } finally {
      setIsFixing(false);
    }
  };

  const predictions = data?.predictions || [];
  const summary = data?.summary;

  // Recalculate stats: exclude HOLD from accuracy, only count directional predictions (BUY/SELL)
  const correctedSummary = summary ? {
    ...summary,
    ml_correct: predictions.filter(p => p.has_outcome && p.ml_direction !== "HOLD" && (p.hit_target || p.ml_correct)).length,
    ml_accuracy: (() => {
      const directionalWithOutcome = predictions.filter(p => p.has_outcome && p.ml_direction !== "HOLD");
      if (directionalWithOutcome.length === 0) return null;
      const correct = directionalWithOutcome.filter(p => p.hit_target || p.ml_correct).length;
      return Math.round(correct / directionalWithOutcome.length * 100);
    })(),
    with_outcome: predictions.filter(p => p.has_outcome && p.ml_direction !== "HOLD").length,
  } : null;

  // Filter predictions - treat hit_target as correct, HOLD as neutral
  const filteredPredictions = predictions.filter((p) => {
    if (filterResult === "all") return true;
    if (filterResult === "pending") return !p.has_outcome;
    if (filterResult === "correct") return p.ml_direction !== "HOLD" && (p.hit_target || p.ml_correct === true);
    if (filterResult === "wrong") return p.has_outcome && p.ml_direction !== "HOLD" && !p.hit_target && p.ml_correct === false;
    return true;
  });

  return (
    <div className="bg-background border border-white/10 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-accent" />
          <h2 className="font-semibold text-white">
            {locale === "en" ? "Prediction History" : "Tahmin Geçmişi"}
          </h2>
          {summary && (
            <span className="text-xs bg-white/10 text-textSecondary px-2 py-0.5 rounded-full">
              {summary.total_predictions} {locale === "en" ? "total" : "toplam"}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2 flex-wrap">
          {/* Filter */}
          <div className="flex items-center gap-1 text-xs">
            <Filter className="w-3 h-3 text-textSecondary" />
            <select
              value={filterResult}
              onChange={(e) => setFilterResult(e.target.value as any)}
              className="bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-white"
            >
              <option value="all">{locale === "en" ? "All" : "Tümü"}</option>
              <option value="correct">{locale === "en" ? "Correct" : "Doğru"}</option>
              <option value="wrong">{locale === "en" ? "Wrong" : "Yanlış"}</option>
              <option value="pending">{locale === "en" ? "Pending" : "Bekliyor"}</option>
            </select>
          </div>
          
          {/* Days */}
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-white"
          >
            <option value={3}>3 {locale === "en" ? "days" : "gün"}</option>
            <option value={7}>7 {locale === "en" ? "days" : "gün"}</option>
            <option value={14}>14 {locale === "en" ? "days" : "gün"}</option>
            <option value={30}>30 {locale === "en" ? "days" : "gün"}</option>
          </select>
          
          {/* Refresh */}
          <button
            onClick={() => refetch()}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
            title={locale === "en" ? "Refresh" : "Yenile"}
          >
            <RefreshCw className={`w-4 h-4 text-textSecondary ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      {correctedSummary && correctedSummary.with_outcome > 0 && (
        <div className="px-4 py-3 border-b border-white/10 bg-white/5">
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-4 text-center text-sm">
            <div>
              <div className="text-2xl font-bold text-white">
                {correctedSummary.ml_accuracy !== null ? `${correctedSummary.ml_accuracy}%` : "-"}
              </div>
              <div className="text-xs text-textSecondary">
                {locale === "en" ? "Real WR" : "Gerçek WR"}
              </div>
              <div className="text-[10px] text-textSecondary opacity-60 mt-0.5">
                {locale === "en" ? "real TPs only" : "gerçek TP hit"}
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold text-success">{correctedSummary.target_hits}</div>
              <div className="text-xs text-textSecondary">
                {locale === "en" ? "Real TP Hits" : "Gerçek TP"}
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold text-warning" style={{ color: "#fbbf24" }}>
                {(correctedSummary as any).window_target_hits ?? 0}
              </div>
              <div className="text-xs text-textSecondary">
                {locale === "en" ? "Window Win" : "Süre Win"}
              </div>
              <div className="text-[10px] text-textSecondary opacity-60 mt-0.5">
                {locale === "en" ? "MFE≥TP1, no fire" : "TP1 değdi, ateşlenmedi"}
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold text-danger">{correctedSummary.stop_hits}</div>
              <div className="text-xs text-textSecondary">
                {locale === "en" ? "Stop Hits" : "Stop Vuruş"}
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-400">{correctedSummary.pending_outcome}</div>
              <div className="text-xs text-textSecondary">
                {locale === "en" ? "Pending" : "Bekliyor"}
              </div>
            </div>
            <div>
              <button
                onClick={handleFixDatabase}
                disabled={isFixing}
                className="text-xs bg-accent/20 text-accent px-2 py-1 rounded hover:bg-accent/30 transition-colors disabled:opacity-50"
                title={locale === "en" ? "Fix database accuracy values" : "Veritabanı doğruluk değerlerini düzelt"}
              >
                {isFixing ? (
                  <RefreshCw className="w-3 h-3 animate-spin inline mr-1" />
                ) : (
                  <CheckCircle className="w-3 h-3 inline mr-1" />
                )}
                {locale === "en" ? "Fix Data" : "Veriyi Düzelt"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-5 h-5 animate-spin text-accent" />
          </div>
        ) : error ? (
          <div className="text-center py-8 text-danger">
            {locale === "en" ? "Failed to load history" : "Geçmiş yüklenemedi"}
          </div>
        ) : filteredPredictions.length === 0 ? (
          <div className="text-center py-8 text-textSecondary">
            {locale === "en" ? "No predictions found" : "Tahmin bulunamadı"}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-xs text-textSecondary uppercase bg-white/5">
              <tr>
                <th className="px-4 py-3 text-left">{locale === "en" ? "Date" : "Tarih"}</th>
                <th className="px-4 py-3 text-left">{locale === "en" ? "Symbol" : "Sembol"}</th>
                <th className="px-4 py-3 text-center">{locale === "en" ? "ML Signal" : "ML Sinyal"}</th>
                <th className="px-4 py-3 text-right">{locale === "en" ? "Entry" : "Giriş"}</th>
                <th className="px-4 py-3 text-right">{locale === "en" ? "Target" : "Hedef"}</th>
                <th className="px-4 py-3 text-right">{locale === "en" ? "Stop" : "Stop"}</th>
                <th className="px-4 py-3 text-center">{locale === "en" ? "Result" : "Sonuç"}</th>
                <th className="px-4 py-3 text-right">{locale === "en" ? "Exit" : "Çıkış"}</th>
                <th className="px-4 py-3 text-right">{locale === "en" ? "P/L %" : "K/Z %"}</th>
                <th className="px-4 py-3 text-center"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredPredictions.map((pred) => (
                <>
                  <tr
                    key={pred.id}
                    className={`hover:bg-white/5 cursor-pointer transition-colors ${
                      expandedRow === pred.id ? "bg-white/5" : ""
                    }`}
                    onClick={() => setExpandedRow(expandedRow === pred.id ? null : pred.id)}
                  >
                    <td className="px-4 py-3 text-white whitespace-nowrap">
                      {formatDate(pred.timestamp, locale)}
                    </td>
                    <td className="px-4 py-3 font-medium text-white">{pred.symbol}</td>
                    <td className="px-4 py-3 text-center">
                      <DirectionBadge direction={pred.ml_direction} />
                      <span className="ml-1 text-xs text-textSecondary">
                        {pred.ml_confidence?.toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-white">
                      {formatPrice(pred.entry_price, pred.symbol)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-success">
                      {formatPrice(pred.target_price, pred.symbol)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-danger">
                      {formatPrice(pred.stop_price, pred.symbol)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <ResultBadge
                        correct={pred.ml_correct}
                        hitTarget={pred.hit_target}
                        hitStop={pred.hit_stop}
                        pending={!pred.has_outcome}
                        direction={pred.ml_direction}
                      />
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-white">
                      {formatPrice(pred.exit_price, pred.symbol)}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono font-medium ${
                      (pred.price_change_pct || 0) >= 0 ? "text-success" : "text-danger"
                    }`}>
                      {pred.price_change_pct !== undefined
                        ? `${pred.price_change_pct >= 0 ? "+" : ""}${pred.price_change_pct.toFixed(2)}%`
                        : "-"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {expandedRow === pred.id ? (
                        <ChevronUp className="w-4 h-4 text-textSecondary" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-textSecondary" />
                      )}
                    </td>
                  </tr>
                  {/* Expanded Row */}
                  {expandedRow === pred.id && (
                    <tr className="bg-white/5">
                      <td colSpan={10} className="px-4 py-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-textSecondary">{locale === "en" ? "Claude Signal:" : "Claude Sinyal:"}</span>
                            <span className="ml-2">
                              {pred.claude_direction ? (
                                <>
                                  <DirectionBadge direction={pred.claude_direction} />
                                  <span className="ml-1 text-xs text-textSecondary">
                                    {pred.claude_confidence?.toFixed(0)}%
                                  </span>
                                </>
                              ) : (
                                <span className="text-textSecondary">-</span>
                              )}
                            </span>
                          </div>
                          <div>
                            <span className="text-textSecondary">{locale === "en" ? "Actual Move:" : "Gerçek Hareket:"}</span>
                            <span className="ml-2">
                              {pred.actual_direction ? (
                                <DirectionBadge direction={pred.actual_direction} />
                              ) : (
                                <span className="text-textSecondary">-</span>
                              )}
                            </span>
                          </div>
                          <div>
                            <span className="text-textSecondary">{locale === "en" ? "High Price:" : "En Yüksek:"}</span>
                            <span className="ml-2 font-mono text-white">
                              {formatPrice(pred.high_price, pred.symbol)}
                            </span>
                          </div>
                          <div>
                            <span className="text-textSecondary">{locale === "en" ? "Low Price:" : "En Düşük:"}</span>
                            <span className="ml-2 font-mono text-white">
                              {formatPrice(pred.low_price, pred.symbol)}
                            </span>
                          </div>
                          {pred.outcome_time && (
                            <div className="col-span-2 md:col-span-4">
                              <span className="text-textSecondary">{locale === "en" ? "Outcome Checked:" : "Sonuç Kontrolü:"}</span>
                              <span className="ml-2 text-white">{formatDate(pred.outcome_time, locale)}</span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Load More */}
      {filteredPredictions.length >= limit && (
        <div className="px-4 py-3 border-t border-white/10 text-center">
          <button
            onClick={() => setLimit(limit + 30)}
            className="text-sm text-accent hover:text-accent/80 transition-colors"
          >
            {locale === "en" ? "Load More" : "Daha Fazla Yükle"}
          </button>
        </div>
      )}
    </div>
  );
}
