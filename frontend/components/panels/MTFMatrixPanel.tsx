"use client";

import { useState, useEffect } from "react";
import { PanelInfoButton } from "../PanelInfoButton";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  RefreshCw,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Minus,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface TimeframeData {
  timeframe?: string;
  current_price?: number;
  trend?: string;
  signal?: string;
  confidence?: number;
  ema?: {
    ema20?: number;
    ema50?: number;
    ema200?: number;
    price_above_ema20?: boolean;
    price_above_ema50?: boolean;
    price_above_ema200?: boolean;
  };
  bollinger?: {
    upper?: number;
    middle?: number;
    lower?: number;
    bandwidth?: number;
    percent_b?: number;
    squeeze?: boolean;
  };
  atr?: { atr14?: number; atr_percent?: number; volatility_level?: string };
  volume?: { volume_ratio?: number; volume_trend?: string; volume_confirmation?: boolean };
  rsi14?: number;
  macd_signal?: string;
}

interface MTFData {
  success: boolean;
  symbol?: string;
  current_price?: number;
  timestamp?: string;
  timeframes?: Record<string, TimeframeData>;
  confluence?: {
    overall_signal?: string;
    overall_confidence?: number;
    bullish_count?: number;
    bearish_count?: number;
    neutral_count?: number;
    alignment_score?: number;
    recommendation?: string;
    risk_level?: string;
    score?: number;
    direction?: string;
    strength?: string;
    agreement_pct?: number;
  };
  error?: string;
}

const SYMBOLS = [
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "CL.COMM", label: "US Oil" },
];

const TF_ORDER = ["M5", "M15", "M30", "H1", "H4", "D1"];
const TF_LABELS: Record<string, string> = { M5: "5m", M15: "15m", M30: "30m", H1: "1H", H4: "4H", D1: "1D" };

export default function MTFMatrixPanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [data, setData] = useState<MTFData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const { data: wsData, wsConnected } = useWSPanelData(symbol, "mtf");

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [symbol]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/mtf/analysis?symbol=${symbol}`);
      const json: MTFData = await res.json();
      setData(json);
      if (json.success) setLastUpdate(new Date());
    } catch (e) {
      console.error("MTF fetch error:", e);
      setData({ success: false, error: "Connection failed" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (wsData) {
      setData(wsData);
      setLastUpdate(new Date());
      setLoading(false);
    }
  }, [wsData]);

  useEffect(() => {
    if (!wsData) fetchData();
    if (!wsConnected) {
      const interval = setInterval(fetchData, 120000);
      return () => clearInterval(interval);
    }
  }, [symbol, wsConnected]);

  const trendColor = (dir?: string) => {
    if (!dir) return "rgba(255,255,255,0.3)";
    const d = dir.toLowerCase();
    if (d.includes("bull") || d.includes("up") || d === "long" || d.includes("buy")) return "#00ff88";
    if (d.includes("bear") || d.includes("down") || d === "short" || d.includes("sell")) return "#ff3366";
    return "#f0b429";
  };

  const emaAlignment = (ema?: TimeframeData["ema"]) => {
    if (!ema) return "mixed";
    const above = [ema.price_above_ema20, ema.price_above_ema50, ema.price_above_ema200].filter(Boolean).length;
    if (above === 3) return "bullish";
    if (above === 0) return "bearish";
    return "mixed";
  };

  const bbPosition = (bb?: TimeframeData["bollinger"]) => {
    if (!bb || bb.percent_b == null) return "—";
    if (bb.squeeze) return "Squeeze";
    if (bb.percent_b > 0.8) return "Upper";
    if (bb.percent_b < 0.2) return "Lower";
    return "Mid";
  };

  const trendIcon = (dir?: string) => {
    if (!dir) return <Minus className="w-3.5 h-3.5" style={{ color: "#f0b429" }} />;
    const d = dir.toLowerCase();
    if (d.includes("bull") || d.includes("up")) return <TrendingUp className="w-3.5 h-3.5" style={{ color: "#00ff88" }} />;
    if (d.includes("bear") || d.includes("down")) return <TrendingDown className="w-3.5 h-3.5" style={{ color: "#ff3366" }} />;
    return <Activity className="w-3.5 h-3.5" style={{ color: "#f0b429" }} />;
  };

  const rsiColor = (rsi?: number) => {
    if (!rsi) return "rgba(255,255,255,0.4)";
    if (rsi > 70) return "#ff3366";
    if (rsi < 30) return "#00ff88";
    if (rsi > 60) return "#f0b429";
    if (rsi < 40) return "#00ccff";
    return "rgba(255,255,255,0.6)";
  };

  const signalBadge = (dir?: string) => {
    if (!dir) return { color: "#f0b429", label: "HOLD", icon: Minus };
    const d = dir.toLowerCase();
    if (d.includes("buy") || d.includes("bull") || d.includes("long")) return { color: "#00ff88", label: "BUY", icon: CheckCircle };
    if (d.includes("sell") || d.includes("bear") || d.includes("short")) return { color: "#ff3366", label: "SELL", icon: XCircle };
    return { color: "#f0b429", label: "HOLD", icon: Minus };
  };

  const confScore = data?.confluence?.overall_confidence ?? data?.confluence?.score ?? 0;
  const confDir = data?.confluence?.overall_signal ?? data?.confluence?.direction ?? "NEUTRAL";
  const confAlign = data?.confluence?.alignment_score ?? data?.confluence?.agreement_pct ?? 0;
  const confluenceColor = confScore > 60 ? "#00ff88" : confScore > 30 ? "#f0b429" : "#ff3366";

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="h-48 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px rgba(0,204,255,0.10), inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(0,204,255,0.2)", boxShadow: "0 0 12px rgba(0,204,255,0.3)" }}>
            <BarChart3 className="w-4 h-4" style={{ color: "#00ccff" }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">MTF Confluence Matrix</h2>
            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>Multi-Timeframe Analiz</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setSymbol(s.key)}
                className="px-2.5 py-1 text-[10px] font-bold font-mono transition-all"
                style={{
                  background: symbol === s.key ? "rgba(0,204,255,0.2)" : "rgba(255,255,255,0.03)",
                  color: symbol === s.key ? "#00ccff" : "rgba(255,255,255,0.4)",
                }}>
                {s.label}
              </button>
            ))}
          </div>
          <button onClick={fetchData} className="p-1.5 rounded-lg" style={{ background: "rgba(255,255,255,0.05)" }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: "rgba(255,255,255,0.35)" }} />
          </button>
          <PanelInfoButton panelId="mtf-matrix" />
        </div>
      </div>

      {!data?.success ? (
        <div className="p-8 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40" style={{ color: "#f0b429" }} />
          <p className="text-sm font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>{data?.error || "Veri yüklenemedi"}</p>
        </div>
      ) : (
        <>
          {/* Confluence Score Banner */}
          {data.confluence && (
            <div className="px-4 py-3 flex items-center justify-between" style={{ background: `${confluenceColor}06` }}>
              <div className="flex items-center gap-3">
                <div className="relative w-14 h-14">
                  <svg className="w-14 h-14 -rotate-90">
                    <circle cx="28" cy="28" r="24" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
                    <circle cx="28" cy="28" r="24" fill="none" stroke={confluenceColor} strokeWidth="4"
                      strokeDasharray={`${(confScore / 100) * 150.8} 150.8`} strokeLinecap="round"
                      style={{ filter: `drop-shadow(0 0 6px ${confluenceColor}60)` }} />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-bold font-mono" style={{ color: confluenceColor }}>{Math.round(confScore)}</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs font-bold font-mono" style={{ color: confluenceColor }}>
                    {confDir.replace(/_/g, " ")} CONFLUENCE
                  </div>
                  <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>
                    Risk: {data.confluence.risk_level || "N/A"} • Uyum: {confAlign.toFixed(0)}%
                  </div>
                </div>
              </div>
              {data.current_price && (
                <div className="text-right">
                  <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Fiyat</div>
                  <div className="text-sm font-bold font-mono text-white/80">{data.current_price?.toFixed(2)}</div>
                </div>
              )}
            </div>
          )}

          {/* Matrix Table */}
          <div className="px-3 py-3">
            {/* Table Header */}
            <div className="grid grid-cols-6 gap-1 mb-1.5 px-1">
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.25)" }}>TF</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.25)" }}>Trend</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.25)" }}>EMA</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.25)" }}>RSI</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.25)" }}>Vol</div>
              <div className="text-[9px] font-mono uppercase tracking-widest text-center" style={{ color: "rgba(255,255,255,0.25)" }}>Sinyal</div>
            </div>

            {/* Table Rows */}
            <div className="space-y-1">
              {TF_ORDER.map((tf) => {
                const tfData = data.timeframes?.[tf];
                if (!tfData) return null;
                const dir = typeof tfData.trend === "string" ? tfData.trend : "";
                const emaAlign = emaAlignment(tfData.ema);
                const sig = signalBadge(tfData.signal || dir);
                const SigIcon = sig.icon;
                const rsiVal = tfData.rsi14;
                const bbPos = bbPosition(tfData.bollinger);
                return (
                  <div key={tf} className="grid grid-cols-6 gap-1 items-center rounded-lg px-2 py-2" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
                    {/* TF */}
                    <div className="text-xs font-bold font-mono text-white/70">{TF_LABELS[tf] || tf}</div>
                    {/* Trend */}
                    <div className="flex items-center gap-1">
                      {trendIcon(dir)}
                      <span className="text-[10px] font-mono" style={{ color: trendColor(dir) }}>
                        {dir?.slice(0, 5) || "—"}
                      </span>
                    </div>
                    {/* EMA Stack */}
                    <div className="text-[10px] font-mono" style={{ color: trendColor(emaAlign) }}>
                      {emaAlign.slice(0, 8)}
                    </div>
                    {/* RSI */}
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] font-bold font-mono" style={{ color: rsiColor(rsiVal) }}>
                        {rsiVal != null ? rsiVal.toFixed(0) : "—"}
                      </span>
                    </div>
                    {/* Volatility */}
                    <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>
                      {bbPos}
                    </div>
                    {/* Signal */}
                    <div className="flex justify-center">
                      <div className="flex items-center gap-1 px-2 py-0.5 rounded-full" style={{ background: `${sig.color}15`, border: `1px solid ${sig.color}25` }}>
                        <SigIcon className="w-2.5 h-2.5" style={{ color: sig.color }} />
                        <span className="text-[9px] font-bold font-mono" style={{ color: sig.color }}>{sig.label}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Conflict Warning */}
          {data.confluence && confAlign < 60 && (
            <div className="px-4 pb-3">
              <div className="rounded-xl p-2.5 flex items-center gap-2" style={{ background: "rgba(240,180,41,0.06)", border: "1px solid rgba(240,180,41,0.12)" }}>
                <AlertTriangle className="w-4 h-4 shrink-0" style={{ color: "#f0b429" }} />
                <p className="text-[10px] font-mono" style={{ color: "#f0b429" }}>
                  Timeframe çelişkisi tespit edildi. Higher TF pullback olabilir - dikkatli olun.
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="px-4 py-2 text-center" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <p className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."} | MTF Analysis
        </p>
      </div>
    </div>
  );
}
