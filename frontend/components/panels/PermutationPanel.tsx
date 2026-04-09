"use client";

import React, { useState, useEffect } from "react";
import ConsensusComboBoard, { type ConsensusSymbolView } from "./ConsensusComboBoard";
const translations: Record<string, Record<string, string>> = {
  tr: {
    title: "Permütasyon Analizi",
    tab_models: "Yapay Zeka Modelleri",
    tab_indicators: "Stratejik Formasyonlar",
    info_title: "Permütasyon Analizi Nedir?",
    info_purpose: "Amac: Her bir sinyalin gercekten ise yarayip yaramadigini 1500 mum geriye donuk olarak kanitlamak.",
    info_how_it_works: "Nasil Calisir: O anki butun indikator kosullari toplanir, tek tek geriye test edilir.",
    info_usage: "Kullanim: En yuksek kazanma orani (win rate) nerede ise ona guven.",
    loading: "Permütasyon hesabı yapılıyor...",
    col_combo: "Kombinasyon (Sinyal)",
    col_signals: "Toplam Sinyal",
    col_winrate: "Kazanma % (Win Rate)",
    col_profit_factor: "Kâr Çarpanı (PF)",
    no_data: "Yeterli sinyal bulunamadı.",
    insufficient_data_tooltip: "Yetersiz Veri (Son 180G)",
    target_target: "Hedef:"
  },
  en: {
    title: "Permutation Analysis",
    tab_models: "AI Models",
    tab_indicators: "Strategic Patterns",
    info_title: "What is Permutation Analysis?",
    info_purpose: "Purpose: To backtest every current signal condition against the last 1500 candles.",
    info_how_it_works: "How it Works: Collects all current conditions and backtests them individually.",
    info_usage: "Usage: Trust the conditions with the highest win rate.",
    loading: "Calculating permutations...",
    col_combo: "Combination (Signal)",
    col_signals: "Total Signals",
    col_winrate: "Win Rate %",
    col_profit_factor: "Profit Factor",
    no_data: "Not enough signals found.",
    insufficient_data_tooltip: "Insufficient Data (Last 180D)",
    target_target: "Target:"
  }
};
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart2,
  Activity,
  RefreshCw,
  Target,
  Clock,
  ChevronDown,
  Layers,
  Info,
  ArrowUpRight,
  ArrowDownRight,
  TriangleAlert
} from "lucide-react";
import { buildApiUrl } from "@/lib/api/base";

const SYMBOLS = [
  { id: "NDX.INDX", label: "NASDAQ" },
  { id: "XAUUSD", label: "XAU/USD" },
  { id: "GDAXI.INDX", label: "DAX" },
  { id: "USOIL.FOREX", label: "US OIL" },
];

interface PermutationPanelProps {
  symbol?: string;
}

interface ModelResult {
  combination: string;
  total_signals: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  insufficient_data?: boolean;
}

interface IndicatorResult {
  indicator_combo: string;
  occurrences: number;
  wins: number;
  win_rate: number;
  timeframe?: string;
  profit_factor?: number;
  insufficient_data?: boolean;
}

interface MetaInfo {
  tgt_pct: number;
  fwd_candles: number;
  days_used: number;
  model_source: string;
  indicator_source: string;
  indicator_timeframe: string;
}

export function PermutationPanel({ symbol: propSymbol }: PermutationPanelProps) {
  const t = (key: keyof typeof translations.tr) => (translations.tr[key] || key) as string;
  const [activeSymbol, setActiveSymbol] = useState(propSymbol || "NDX.INDX");
  const [activeTab, setActiveTab] = useState<"models" | "indicators">("models");
  const [direction, setDirection] = useState<"BUY" | "SELL">("BUY");
  const [showInfo, setShowInfo] = useState(false);
  const isSymbolLocked = Boolean(propSymbol);
  const symbol = activeSymbol;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modelsData, setModelsData] = useState<ModelResult[]>([]);
  const [indicatorsData, setIndicatorsData] = useState<IndicatorResult[]>([]);
  const [consensusData, setConsensusData] = useState<ConsensusSymbolView | null>(null);
  const [metaInfo, setMetaInfo] = useState<MetaInfo>({
    tgt_pct: 0.3,
    fwd_candles: 5,
    days_used: 30,
    model_source: "live",
    indicator_source: "live",
    indicator_timeframe: "-"
  });

  const fetchPermutations = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const url = buildApiUrl(`/api/permutation-analysis/${symbol}?direction=${direction}&analysis_type=both&source=auto&min_occurrences=5&cluster_window_minutes=10&lookforward_candles=5&target_move_pct=0.3&lookback_days=365`);
      const consensusUrl = buildApiUrl(`/api/permutation-analysis/consensus/${symbol}?top=6`);
      const [res, consensusRes] = await Promise.all([
        fetch(url),
        fetch(consensusUrl),
      ]);
      if (!res.ok) throw new Error("Failed to fetch permutation data");
      const json = await res.json();
      if (consensusRes.ok) {
        const consensusJson = await consensusRes.json();
        if (consensusJson?.success && consensusJson.data) {
          setConsensusData(consensusJson.data as ConsensusSymbolView);
        } else {
          setConsensusData(null);
        }
      } else {
        setConsensusData(null);
      }

      if (json.success) {
        const modelsAnalysis = json.data.models_analysis || {};
        const indicatorsAnalysis = json.data.indicators_analysis || {};
        const modelResults = modelsAnalysis.results || [];
        const indicatorResults = indicatorsAnalysis.results || [];
        const nestedErrors = [
          modelsAnalysis.error,
          indicatorsAnalysis.error,
        ].filter(Boolean);
        const firstIndicatorTimeframe = indicatorResults.find((row: IndicatorResult) => row?.timeframe)?.timeframe;

        setModelsData(modelResults);
        setIndicatorsData(indicatorResults);
        setMetaInfo({
          tgt_pct: indicatorsAnalysis.target_move_pct || 0.3,
          fwd_candles: indicatorsAnalysis.lookforward_candles || 5,
          days_used: modelsAnalysis.lookback_days_used || 30,
          model_source: modelsAnalysis.source || "live",
          indicator_source: indicatorsAnalysis.source || "live",
          indicator_timeframe: indicatorsAnalysis.timeframe_used || firstIndicatorTimeframe || "-"
        });
        if (nestedErrors.length > 0 && modelResults.length === 0 && indicatorResults.length === 0) {
          setError(nestedErrors.join(', '));
        }
      } else {
        setError(json.error || "Unknown error");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      fetchPermutations();
    }
  }, [symbol, direction]);

  useEffect(() => {
    if (propSymbol) setActiveSymbol(propSymbol);
  }, [propSymbol]);

  return (
    <div className="bg-[#141C2B] rounded-xl border border-white/5 overflow-hidden flex flex-col mt-4">
      {/* HEADER */}
      <div className="flex items-center justify-between p-4 border-b border-white/5 bg-[#0B0F17]/50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Layers className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-[16px] tracking-tight">{t("title")}</h3>
            <p className="text-[#6B7280] text-[12px] uppercase font-medium tracking-wide">
              {symbol} • Data: {metaInfo.days_used}D • Models: {metaInfo.model_source} • Indicators: {metaInfo.indicator_source}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Direction Toggle */}
          <div className="flex bg-[#0B0F17] rounded-lg p-1 border border-white/5">
            <button
              onClick={() => setDirection("BUY")}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${direction === "BUY"
                  ? "bg-emerald-500/20 text-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.15)]"
                  : "text-gray-500 hover:text-gray-300"
                }`}
            >
              BUY
            </button>
            <button
              onClick={() => setDirection("SELL")}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${direction === "SELL"
                  ? "bg-red-500/20 text-red-400 shadow-[0_0_8px_rgba(239,68,68,0.15)]"
                  : "text-gray-500 hover:text-gray-300"
                }`}
            >
              SELL
            </button>
          </div>

          <button
            onClick={() => setShowInfo(!showInfo)}
            className={`p-2 rounded-lg transition-colors ${showInfo ? "bg-blue-500/20 text-blue-400" : "bg-white/5 hover:bg-white/10 text-gray-400"}`}
          >
            <Info className="w-4 h-4" />
          </button>

          <button
            onClick={fetchPermutations}
            disabled={isLoading}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-400 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* SYMBOL TABS */}
      {!isSymbolLocked && (
        <div className="flex items-center gap-1 px-4 py-2 border-b border-white/5 bg-[#0D1117]">
          {SYMBOLS.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSymbol(s.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeSymbol === s.id
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : "text-gray-500 hover:text-gray-300 hover:bg-white/5 border border-transparent"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* TABS */}
      <div className="flex border-b border-white/5 bg-[#111827]">
        <button
          onClick={() => setActiveTab("models")}
          className={`relative px-6 py-3 text-sm font-medium transition-colors ${activeTab === "models" ? "text-blue-400" : "text-gray-400 hover:text-gray-200"
            }`}
        >
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            {t("tab_models")}
          </div>
          {activeTab === "models" && (
            <motion.div layoutId="perm-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
          )}
        </button>
        <button
          onClick={() => setActiveTab("indicators")}
          className={`relative px-6 py-3 text-sm font-medium transition-colors ${activeTab === "indicators" ? "text-blue-400" : "text-gray-400 hover:text-gray-200"
            }`}
        >
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            {t("tab_indicators")}
          </div>
          {activeTab === "indicators" && (
            <motion.div layoutId="perm-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
          )}
        </button>
      </div>

      {/* CONTENT ZONE */}
      <div className="p-4 min-h-[300px]">
        {/* INFO BANNER */}
        <AnimatePresence>
          {showInfo && (
            <motion.div
              initial={{ height: 0, opacity: 0, marginBottom: 0 }}
              animate={{ height: "auto", opacity: 1, marginBottom: 16 }}
              exit={{ height: 0, opacity: 0, marginBottom: 0 }}
              className="overflow-hidden"
            >
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 text-sm">
                <div className="flex items-center gap-2 mb-2 text-blue-400 font-semibold">
                  <Info className="w-4 h-4" />
                  {t("info_title")}
                </div>
                <div className="space-y-3 text-[#9AA4B2] leading-relaxed">
                  <p><strong className="text-white/80">{(t("info_purpose") || "").split(":")[0]}:</strong> {(t("info_purpose") || "").split(":").slice(1).join(":")}</p>
                  <p><strong className="text-white/80">{(t("info_how_it_works") || "").split(":")[0]}:</strong> {(t("info_how_it_works") || "").split(":").slice(1).join(":")}</p>
                  <p><strong className="text-white/80">{(t("info_usage") || "").split(":")[0]}:</strong> {(t("info_usage") || "").split(":").slice(1).join(":")}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-48 space-y-4">
            <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />
            <p className="text-gray-500 text-sm">{t("loading")}</p>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-48 text-red-400 text-sm">
            {error}
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {activeTab === "models" && (
              <motion.div
                key="models-panel"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                {consensusData && <ConsensusComboBoard data={consensusData} maxRows={4} />}
                <div className="rounded-xl border border-white/5 bg-[#0B0F17]/40 overflow-x-auto">
                  <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-[#6B7280]">Live model ranking</div>
                      <div className="text-sm text-[#E6EDF3] font-medium">{direction} yönü için klasik permutation tablosu</div>
                    </div>
                    {consensusData?.parameters && (
                      <div className="text-[11px] text-[#6B7280] text-right">
                        {consensusData.parameters.lookback_days}D • {consensusData.parameters.bucket_minutes}m bucket
                      </div>
                    )}
                  </div>
                  {modelsData.length === 0 ? (
                    <div className="text-center text-gray-500 py-10 text-sm">{t("no_data")}</div>
                  ) : (
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-white/5">
                          <th className="pb-3 pt-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium pl-4">{t("col_combo")}</th>
                          <th className="pb-3 pt-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium text-right">{t("col_signals")}</th>
                          <th className="pb-3 pt-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium text-right">{t("col_winrate")}</th>
                          <th className="pb-3 pt-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium text-right pr-4">{t("col_profit_factor")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modelsData.map((row, idx) => (
                          <tr key={idx}
                            className={`border-b border-white/5 hover:bg-white/[0.02] transition-colors ${row.insufficient_data ? 'opacity-50 saturate-50' : ''}`}
                            title={row.insufficient_data ? t("insufficient_data_tooltip") || "Yetersiz Veri (Son 180G)" : undefined}
                          >
                            <td className="py-3 pl-4">
                              <div className="flex flex-wrap gap-1.5 items-center">
                                {row.insufficient_data && <TriangleAlert className="w-3.5 h-3.5 text-yellow-500 mr-1" />}
                                {(row.combination || "").split('+').map((m: string, i: number) => (
                                  <span key={i} className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-xs font-semibold uppercase border border-blue-500/20 shadow-[0_0_8px_rgba(79,140,255,0.05)]">
                                    {m}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="py-3 text-right text-sm text-[#9AA4B2] font-medium bg-black/20">
                              {row.total_signals}
                            </td>
                            <td className="py-3 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <div className="w-12 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                  <div
                                    className="h-full rounded-full"
                                    style={{
                                      width: `${(row.win_rate || 0) * 100}%`,
                                      backgroundColor: (row.win_rate || 0) >= 0.5 ? '#16C784' : '#EA3943',
                                      opacity: 0.9
                                    }}
                                  />
                                </div>
                                <span className={`text-sm font-bold w-12 text-right ${(row.win_rate || 0) >= 0.5 ? "text-[#16C784]" : "text-[#EA3943]"}`}>
                                  {((row.win_rate || 0) * 100).toFixed(1)}%
                                </span>
                              </div>
                            </td>
                            <td className="py-3 text-right pr-4">
                              <span className={`text-sm font-bold ${(row.profit_factor || 0) >= 1.5 ? "text-[#16C784]" : (row.profit_factor || 0) >= 1.0 ? "text-white" : "text-[#EA3943]"}`}>
                                {(row.profit_factor === 999.0 || !row.profit_factor) ? "∞" : (row.profit_factor || 0).toFixed(2)}x
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "indicators" && (
              <motion.div
                key="ind-panel"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                {/* Meta header for the analysis rule */}
                <div className="mb-4 text-xs text-[#9AA4B2] bg-white/5 p-3 rounded-lg border border-white/5 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 opacity-70" />
                    {metaInfo.fwd_candles} Candles Forward Look • TF: {metaInfo.indicator_timeframe}
                  </span>
                  <span className="flex items-center gap-1.5 text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">
                    {direction === "BUY" ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                    {t("target_target")} {metaInfo.tgt_pct}% Move
                  </span>
                </div>

                {indicatorsData.length === 0 ? (
                  <div className="text-center text-gray-500 py-10 text-sm">{t("no_data")}</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-white/5">
                          <th className="pb-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium pl-2">{t("col_combo")} (Conditions)</th>
                          <th className="pb-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium text-right">{t("col_signals")} (Occurrences)</th>
                          <th className="pb-3 text-xs uppercase tracking-wider text-[#6B7280] font-medium text-right pr-2">{t("col_winrate")} <br /><span className="text-[10px] opacity-60">Hits TP</span></th>
                        </tr>
                      </thead>
                      <tbody>
                        {indicatorsData.map((row, idx) => (
                          <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                            <td className="py-3 pl-2">
                              <div className="flex flex-wrap gap-1.5">
                                {(row.indicator_combo || "").split(' AND ').map((cond: string, i: number) => {
                                  let bgClass = "bg-white/5 text-gray-300 border-white/10";
                                  if (cond.includes("RSI>70") || cond.includes("EMA20Dist>+1%")) bgClass = "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
                                  if (cond.includes("RSI<30") || cond.includes("EMA20Dist<-1%")) bgClass = "bg-purple-500/10 text-purple-400 border-purple-500/20";
                                  if (cond.includes("Vol") && !cond.includes("<0.7")) bgClass = "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";

                                  return (
                                    <span key={i} className={`px-2 py-0.5 rounded text-xs font-semibold border ${bgClass}`}>
                                      {cond}
                                    </span>
                                  )
                                })}
                              </div>
                            </td>
                            <td className="py-3 text-right text-sm text-[#9AA4B2] font-medium bg-black/20">
                              {row.occurrences}
                            </td>
                            <td className="py-3 text-right pr-2">
                              <div className="flex items-center justify-end gap-2">
                                <div className="w-12 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                  <div
                                    className="h-full rounded-full"
                                    style={{
                                      width: `${(row.win_rate || 0) * 100}%`,
                                      backgroundColor: (row.win_rate || 0) >= 0.55 ? '#16C784' : (row.win_rate || 0) >= 0.45 ? '#F5A623' : '#EA3943',
                                      opacity: 0.9
                                    }}
                                  />
                                </div>
                                <span className={`text-sm font-bold w-12 text-right ${(row.win_rate || 0) >= 0.55 ? "text-[#16C784]" : (row.win_rate || 0) >= 0.45 ? "text-[#F5A623]" : "text-[#EA3943]"}`}>
                                  {((row.win_rate || 0) * 100).toFixed(1)}%
                                </span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
