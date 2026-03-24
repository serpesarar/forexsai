"use client";

import { useEffect, useState, useCallback } from "react";
import { PanelInfoButton } from "./PanelInfoButton";
import {
  Users,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  Activity,
  Gauge,
  BarChart3,
  ChevronDown,
  Shield,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { InfoClickable, InfoBadge } from "./InfoTooltip";
import { useI18nStore } from "../lib/i18n/store";
import { getApiBase } from "../lib/api/base";

// ═══════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════

interface COTData {
  report_date: string;
  symbol: string;
  commercials_long: number;
  commercials_short: number;
  commercials_net: number;
  commercials_net_change: number;
  speculators_long: number;
  speculators_short: number;
  speculators_net: number;
  speculators_net_change: number;
  spec_long_percent: number;
  spec_positioning_percentile: number;
  total_open_interest: number;
  oi_change_pct: number;
  confidence_adjustment: number;
  signal: "BULLISH" | "BEARISH" | "NEUTRAL" | "TREND_EXHAUSTION";
  reason: string;
  data_source: string;
}

interface SlippageStats {
  average_slippage: number;
  max_slippage: number;
  favorable_count: number;
  unfavorable_count: number;
  total_trades: number;
  position_multiplier: number;
  high_slippage_mode: boolean;
}

// ═══════════════════════════════════════════════════════════════════
// Symbol Configuration
// ═══════════════════════════════════════════════════════════════════

const SYMBOLS = [
  { key: "XAUUSD", label: "GOLD", icon: "🥇", color: "amber" },
  { key: "NASDAQ", label: "NASDAQ", icon: "📊", color: "blue" },
  { key: "DAX", label: "DAX", icon: "🇩🇪", color: "purple" },
  { key: "USOIL", label: "WTI OIL", icon: "🛢️", color: "red" },
];

const API_BASE = getApiBase();

// ═══════════════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════════════

function formatNet(val: number): string {
  const sign = val >= 0 ? "+" : "";
  if (Math.abs(val) >= 1000) {
    return `${sign}${(val / 1000).toFixed(0)}K`;
  }
  return `${sign}${val.toLocaleString()}`;
}

function getSignalColor(signal: string): string {
  switch (signal) {
    case "BULLISH": return "text-green-400";
    case "BEARISH": return "text-red-400";
    case "TREND_EXHAUSTION": return "text-orange-400";
    default: return "text-gray-400";
  }
}

function getSignalBg(signal: string): string {
  switch (signal) {
    case "BULLISH": return "bg-green-900/30 border-green-500/30";
    case "BEARISH": return "bg-red-900/30 border-red-500/30";
    case "TREND_EXHAUSTION": return "bg-orange-900/30 border-orange-500/30";
    default: return "bg-gray-800/50 border-gray-600/30";
  }
}

// ═══════════════════════════════════════════════════════════════════
// COT Card Component
// ═══════════════════════════════════════════════════════════════════

function COTCard({ data, symbolInfo }: { data: COTData; symbolInfo: typeof SYMBOLS[0] }) {
  const { t } = useI18nStore();
  const isBullish = data.signal === "BULLISH";
  const isBearish = data.signal === "BEARISH";
  const isExhaustion = data.signal === "TREND_EXHAUSTION";

  return (
    <div className={`rounded-lg p-3 border ${getSignalBg(data.signal)}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{symbolInfo.icon}</span>
          <span className="text-sm font-bold text-white">{symbolInfo.label} COT</span>
          <InfoBadge infoKey="cot_speculators" />
        </div>
        <InfoClickable infoKey="cot_speculators">
          <span className={`text-xs font-bold px-2 py-0.5 rounded ${getSignalColor(data.signal)} cursor-help`}>
            {data.signal}
          </span>
        </InfoClickable>
      </div>

      {/* Commercials vs Speculators */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        {/* Commercials (Smart Money) */}
        <InfoClickable infoKey="cot_commercials">
          <div className="bg-slate-800/60 rounded-lg p-2.5 border border-white/5 cursor-help hover:bg-slate-700/60 transition-colors">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Shield className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-[10px] text-gray-400 font-medium">{t("cot.commercials")}</span>
            </div>
            <div className={`text-base font-bold font-mono ${data.commercials_net > 0 ? "text-green-400" : "text-red-400"}`}>
              {formatNet(data.commercials_net)}
            </div>
            {data.commercials_net_change !== 0 && (
              <div className="flex items-center gap-1 mt-0.5">
                {data.commercials_net_change > 0
                  ? <ArrowUpRight className="w-3 h-3 text-green-400" />
                  : <ArrowDownRight className="w-3 h-3 text-red-400" />}
                <span className={`text-[10px] font-mono ${data.commercials_net_change > 0 ? "text-green-400" : "text-red-400"}`}>
                  {formatNet(data.commercials_net_change)} WoW
                </span>
              </div>
            )}
          </div>
        </InfoClickable>

        {/* Speculators (Crowd) */}
        <InfoClickable infoKey="cot_speculators">
          <div className="bg-slate-800/60 rounded-lg p-2.5 border border-white/5 cursor-help hover:bg-slate-700/60 transition-colors">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Users className="w-3.5 h-3.5 text-purple-400" />
              <span className="text-[10px] text-gray-400 font-medium">{t("cot.speculators")}</span>
            </div>
            <div className={`text-base font-bold font-mono ${data.speculators_net > 0 ? "text-green-400" : "text-red-400"}`}>
              {formatNet(data.speculators_net)}
            </div>
            {data.speculators_net_change !== 0 && (
              <div className="flex items-center gap-1 mt-0.5">
                {data.speculators_net_change > 0
                  ? <ArrowUpRight className="w-3 h-3 text-green-400" />
                  : <ArrowDownRight className="w-3 h-3 text-red-400" />}
                <span className={`text-[10px] font-mono ${data.speculators_net_change > 0 ? "text-green-400" : "text-red-400"}`}>
                  {formatNet(data.speculators_net_change)} WoW
                </span>
              </div>
            )}
          </div>
        </InfoClickable>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-slate-800/40 rounded-lg p-2 border border-white/5">
          <div className="text-[10px] text-gray-500">{t("cot.specLong")}</div>
          <div className="text-sm font-bold text-white">{data.spec_long_percent.toFixed(0)}%</div>
          <div className="text-[9px] text-gray-600">P{data.spec_positioning_percentile.toFixed(0)}</div>
        </div>
        <div className="bg-slate-800/40 rounded-lg p-2 border border-white/5">
          <div className="text-[10px] text-gray-500">{t("cot.openInterest")}</div>
          <div className="text-sm font-bold text-white">{(data.total_open_interest / 1000).toFixed(0)}K</div>
          <div className={`text-[9px] font-mono ${data.oi_change_pct > 0 ? "text-green-400" : data.oi_change_pct < 0 ? "text-red-400" : "text-gray-600"}`}>
            {data.oi_change_pct > 0 ? "+" : ""}{data.oi_change_pct.toFixed(1)}%
          </div>
        </div>
        <div className="bg-slate-800/40 rounded-lg p-2 border border-white/5">
          <div className="text-[10px] text-gray-500">{t("cot.adjustment")}</div>
          <div className={`text-sm font-bold ${data.confidence_adjustment > 0 ? "text-green-400" : data.confidence_adjustment < 0 ? "text-red-400" : "text-gray-400"}`}>
            {data.confidence_adjustment > 0 ? "+" : ""}{(data.confidence_adjustment * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Warning for Trend Exhaustion */}
      {isExhaustion && (
        <div className="mt-2 flex items-center gap-2 text-xs text-orange-400 bg-orange-500/10 rounded-lg p-2">
          <AlertTriangle className="w-3 h-3" />
          <span>{data.reason}</span>
        </div>
      )}

      {/* Data Source */}
      <div className="flex items-center justify-between text-[9px] text-gray-600 mt-2 pt-2 border-t border-white/5">
        <span>{data.report_date}</span>
        <span className={data.data_source === "live" ? "text-green-500" : "text-yellow-500"}>
          {data.data_source === "live" ? "● Live CFTC" : "● Fallback"}
        </span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// Main Panel
// ═══════════════════════════════════════════════════════════════════

export default function InstitutionalDataPanel({ className = "" }: { className?: string }) {
  const { t, locale } = useI18nStore();
  const isEn = locale === "en";
  
  const [cotData, setCotData] = useState<Record<string, COTData> | null>(null);
  const [slippageData, setSlippageData] = useState<SlippageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("XAUUSD");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);

      // Fetch COT and Slippage data in parallel
      const [cotRes, slippageRes] = await Promise.all([
        fetch(`${API_BASE}/api/cot/summary`),
        fetch(`${API_BASE}/api/slippage/stats`),
      ]);

      if (cotRes.ok) {
        const cotJson = await cotRes.json();
        if (cotJson.success) {
          // Filter only the symbols we want
          const filtered: Record<string, COTData> = {};
          SYMBOLS.forEach(sym => {
            if (cotJson.data[sym.key]) {
              filtered[sym.key] = cotJson.data[sym.key];
            }
          });
          setCotData(filtered);
        }
      }

      if (slippageRes.ok) {
        const slippageJson = await slippageRes.json();
        if (slippageJson.success) {
          setSlippageData(slippageJson.data);
        }
      }

      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : isEn ? "Unknown error" : "Bilinmeyen hata");
    } finally {
      setLoading(false);
    }
  }, [isEn]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !cotData) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4 ${className}`}>
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="w-6 h-6 animate-spin text-amber-400" />
        </div>
      </div>
    );
  }

  const currentSymbolInfo = SYMBOLS.find(s => s.key === selectedSymbol) || SYMBOLS[0];
  const currentCotData = cotData?.[selectedSymbol];

  return (
    <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden ${className}`}>
      {/* Header with Symbol Selector */}
      <div className="bg-gradient-to-r from-amber-900/50 to-orange-900/50 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-amber-400" />
            <span className="font-semibold text-white">{isEn ? "Institutional Data" : "Kurumsal Veri"}</span>
            
            {/* Symbol Selector */}
            <div className="relative ml-2">
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="appearance-none bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-amber-500/50 cursor-pointer min-w-[120px]"
              >
                {SYMBOLS.map((s) => (
                  <option key={s.key} value={s.key}>
                    {s.icon} {s.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={fetchData}
              className="p-1.5 hover:bg-gray-700/50 rounded-lg transition-colors"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <PanelInfoButton panelId="institutional-data" />
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Slippage Monitor */}
        {slippageData && (
          <div className={`rounded-lg p-3 border ${slippageData.high_slippage_mode ? 'bg-red-900/20 border-red-500/30' : 'bg-gray-800/50 border-gray-700/30'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Gauge className={`w-4 h-4 ${slippageData.high_slippage_mode ? 'text-red-400' : 'text-cyan-400'}`} />
              <span className="text-xs text-gray-400">{isEn ? "Slippage Monitor" : "Kayma Monitörü"}</span>
              <InfoBadge infoKey="slippage" />
              {slippageData.high_slippage_mode && (
                <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full ml-auto">
                  ⚠️ {isEn ? "HIGH" : "YÜKSEK"}
                </span>
              )}
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <InfoClickable infoKey="slippage">
                <div>
                  <div className={`text-lg font-bold ${slippageData.average_slippage > 3 ? 'text-red-400' : slippageData.average_slippage > 1.5 ? 'text-yellow-400' : 'text-green-400'}`}>
                    {slippageData.average_slippage.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">{isEn ? "Avg Pips" : "Ort Pip"}</div>
                </div>
              </InfoClickable>
              <div>
                <div className="text-lg font-bold text-white">
                  {(slippageData.position_multiplier * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">{isEn ? "Position Size" : "Pozisyon"}</div>
              </div>
              <div>
                <div className="text-lg font-bold text-gray-300">
                  {slippageData.total_trades}
                </div>
                <div className="text-xs text-gray-500">{isEn ? "Trades" : "İşlem"}</div>
              </div>
            </div>

            {slippageData.total_trades > 0 && (
              <div className="mt-2 flex items-center justify-center gap-4 text-xs">
                <span className="text-green-400">
                  ✓ {slippageData.favorable_count} {isEn ? "favorable" : "olumlu"}
                </span>
                <span className="text-red-400">
                  ✗ {slippageData.unfavorable_count} {isEn ? "unfavorable" : "olumsuz"}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Selected Symbol COT Data */}
        {currentCotData ? (
          <COTCard data={currentCotData} symbolInfo={currentSymbolInfo} />
        ) : (
          <div className="text-center py-6 text-gray-500 text-sm">
            {error ? `${isEn ? "Error" : "Hata"}: ${error}` : (isEn ? "No COT data available" : "COT verisi mevcut değil")}
          </div>
        )}

        {/* Legend */}
        <div className="text-xs text-gray-500 text-center pt-2 border-t border-gray-700/30">
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <span>📊 {isEn ? "COT: CFTC Weekly Data" : "COT: CFTC Haftalık Veri"}</span>
            <span>|</span>
            <span>⚡ {isEn ? "Updates Friday" : "Cuma Güncellenir"}</span>
            <span>|</span>
            <span>🛡️ {isEn ? "Commercials = Smart Money" : "Commercials = Akıllı Para"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
