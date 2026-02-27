"use client";

import { useState, useEffect } from "react";
import { PanelHeader } from "../PanelHeader";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  ArrowUpIcon as TrendingUp,
  ArrowDownIcon as TrendingDown,
  ActivityIcon as Activity,
  MinusIcon as Minus,
  AlertIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle,
  CloseIcon as XCircle,
} from "../ui/CustomIcons";
import { LayoutGrid } from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
const P = { bg: "var(--bg-primary)", card: "var(--bg-card)", surface: "var(--bg-surface)", border: "var(--border-subtle)", text: "var(--text-primary)", muted: "var(--text-muted)", green: "var(--accent-positive)", red: "var(--accent-negative)", warn: "var(--accent-warning)", accent: "var(--accent-info)" };

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
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
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
    if (!dir) return P.muted;
    const d = dir.toLowerCase();
    if (d.includes("bull") || d.includes("up") || d === "long" || d.includes("buy")) return P.green;
    if (d.includes("bear") || d.includes("down") || d === "short" || d.includes("sell")) return P.red;
    return P.warn;
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
    if (!dir) return <Minus className="w-3.5 h-3.5" style={{ color: P.warn }} />;
    const d = dir.toLowerCase();
    if (d.includes("bull") || d.includes("up")) return <TrendingUp className="w-3.5 h-3.5" style={{ color: P.green }} />;
    if (d.includes("bear") || d.includes("down")) return <TrendingDown className="w-3.5 h-3.5" style={{ color: P.red }} />;
    return <Activity className="w-3.5 h-3.5" style={{ color: P.warn }} />;
  };

  const rsiColor = (rsi?: number) => {
    if (!rsi) return P.muted;
    if (rsi > 70) return P.red;
    if (rsi < 30) return P.green;
    if (rsi > 60) return P.warn;
    if (rsi < 40) return P.accent;
    return P.text;
  };

  const signalBadge = (dir?: string) => {
    if (!dir) return { color: P.warn, label: "HOLD", icon: Minus };
    const d = dir.toLowerCase();
    if (d.includes("buy") || d.includes("bull") || d.includes("long")) return { color: P.green, label: "BUY", icon: CheckCircle };
    if (d.includes("sell") || d.includes("bear") || d.includes("short")) return { color: P.red, label: "SELL", icon: XCircle };
    return { color: P.warn, label: "HOLD", icon: Minus };
  };

  const confScore = data?.confluence?.overall_confidence ?? data?.confluence?.score ?? 0;
  const confDir = data?.confluence?.overall_signal ?? data?.confluence?.direction ?? "NEUTRAL";
  const confAlign = data?.confluence?.alignment_score ?? data?.confluence?.agreement_pct ?? 0;
  const confluenceColor = confScore > 60 ? P.green : confScore > 30 ? P.warn : P.red;

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: "var(--bg-hover)" }} />
        <div className="h-48 rounded-xl" style={{ background: "var(--bg-hover)" }} />
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: P.bg, border: `1px solid ${P.border}`, boxShadow: "0 0 40px var(--accent-info-10), inset 0 1px 0 rgba(255,255,255,0.04)" }}>

      <PanelHeader
        title="MTF CONFLUENCE"
        subtitle="MATRIX"
        icon={<LayoutGrid size={24} strokeWidth={2.5} />}
        iconColor="var(--accent-cyan)"
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        symbols={SYMBOLS}
        activeSymbol={symbol}
        onSymbolChange={setSymbol}
        onRefresh={fetchData}
        loading={loading}
        panelId="mtf-matrix"
      />

      {!data?.success ? (
        <div className="p-8 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40" style={{ color: P.warn }} />
          <p className="text-sm font-mono" style={{ color: P.muted }}>{data?.error || "Veri yüklenemedi"}</p>
        </div>
      ) : (
        <>
          {/* Confluence Score Banner */}
          {data.confluence && (
            <div className="px-4 py-3 flex items-center justify-between" style={{ background: `${confluenceColor}06` }}>
              <div className="flex items-center gap-3">
                <div className="relative w-14 h-14">
                  <svg className="w-14 h-14 -rotate-90">
                    <circle cx="28" cy="28" r="24" fill="none" stroke={P.border} strokeWidth="3" />
                    <circle cx="28" cy="28" r="24" fill="none" stroke={confluenceColor} strokeWidth="3"
                      strokeDasharray={`${(confScore / 100) * 150.8} 150.8`} strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span style={{ fontFamily: FONT, fontSize: 14, fontWeight: 700, color: confluenceColor }}>{Math.round(confScore)}</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs font-bold font-mono" style={{ color: confluenceColor }}>
                    {confDir.replace(/_/g, " ")} CONFLUENCE
                  </div>
                  <div className="text-[10px] font-mono" style={{ color: P.muted }}>
                    Risk: {data.confluence.risk_level || "N/A"} • Uyum: {confAlign.toFixed(0)}%
                  </div>
                </div>
              </div>
              {data.current_price && (
                <div className="text-right">
                  <div className="text-[10px] font-mono" style={{ color: P.muted }}>Fiyat</div>
                  <div className="text-sm font-bold font-mono text-white/80">{data.current_price?.toFixed(2)}</div>
                </div>
              )}
            </div>
          )}

          {/* Matrix Table */}
          <div className="px-3 py-3">
            {/* Table Header */}
            <div className="grid grid-cols-6 gap-1 mb-1.5 px-1">
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: P.muted }}>TF</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: P.muted }}>Trend</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: P.muted }}>EMA</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: P.muted }}>RSI</div>
              <div className="text-[9px] font-mono uppercase tracking-widest" style={{ color: P.muted }}>Vol</div>
              <div className="text-[9px] font-mono uppercase tracking-widest text-center" style={{ color: P.muted }}>Sinyal</div>
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
                  <div key={tf} className="grid grid-cols-6 gap-1 items-center rounded-lg px-2 py-2" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
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
                    <div className="text-[10px] font-mono" style={{ color: P.muted }}>
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
              <div className="rounded-xl p-2.5 flex items-center gap-2" style={{ background: "var(--accent-warning-06)", border: "1px solid var(--accent-warning-12)" }}>
                <AlertTriangle className="w-4 h-4 shrink-0" style={{ color: P.warn }} />
                <p className="text-[10px] font-mono" style={{ color: P.warn }}>
                  Timeframe çelişkisi tespit edildi. Higher TF pullback olabilir - dikkatli olun.
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="px-4 py-2 text-center" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid var(--border-subtle)" }}>
        <p className="text-[10px] font-mono" style={{ color: P.muted }}>
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."} | MTF Analysis
        </p>
      </div>
    </div>
  );
}
