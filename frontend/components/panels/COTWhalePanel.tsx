"use client";

import { useState, useEffect } from "react";
import { PanelHeader } from "../PanelHeader";
import {
  Fish,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  BarChart2,
  Users,
  Building,
  User,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

// ── Theme-aware Color Palette (CSS Variables) ───────────────────────────────
const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  purple: "var(--accent-purple)",
};

interface COTData {
  success: boolean;
  data?: {
    symbol?: string;
    net_non_commercial?: number;
    net_commercial?: number;
    net_small_spec?: number;
    change_non_commercial?: number;
    change_commercial?: number;
    change_small_spec?: number;
    percentile_52w?: number;
    extreme_positioning?: boolean;
    report_date?: string;
    open_interest?: number;
    oi_change?: number;
  };
  error?: string;
}

interface WhaleData {
  success: boolean;
  data?: {
    symbol?: string;
    large_order_flow?: string;
    smart_money_direction?: string;
    whale_accumulation?: boolean;
    whale_distribution?: boolean;
    dark_pool_activity?: string;
    institutional_bias?: string;
    confidence?: number;
    last_large_trade?: { direction: string; size: string; price: number };
  };
  error?: string;
}

const SYMBOLS = [
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "CL.COMM", label: "US Oil" },
];

export default function COTWhalePanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [cotData, setCotData] = useState<COTData | null>(null);
  const [whaleData, setWhaleData] = useState<WhaleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [cotRes, whaleRes] = await Promise.all([
        fetch(`${API_BASE}/api/cot/${symbol}`).then(r => r.json()).catch(() => ({ success: false })),
        fetch(`${API_BASE}/api/whale/${symbol}`).then(r => r.json()).catch(() => ({ success: false })),
      ]);
      setCotData(cotRes);
      setWhaleData(whaleRes);
      setLastUpdate(new Date());
    } catch (e) {
      console.error("COT/Whale fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000); // COT updates weekly, no need for frequent polling
    return () => clearInterval(interval);
  }, [symbol]);

  const dirColor = (d?: string) => {
    if (!d) return P.muted;
    const l = d.toLowerCase();
    if (l.includes("bull") || l.includes("buy") || l.includes("long") || l.includes("accumul")) return P.green;
    if (l.includes("bear") || l.includes("sell") || l.includes("short") || l.includes("distrib")) return P.red;
    return P.warn;
  };

  const percentileColor = (p?: number) => {
    if (!p) return P.purple;
    if (p > 80) return P.red;
    if (p < 20) return P.green;
    return P.warn;
  };

  const netColor = (n?: number) => {
    if (!n) return P.muted;
    return n > 0 ? P.green : P.red;
  };

  const changeArrow = (c?: number) => {
    if (!c) return null;
    return c > 0
      ? <TrendingUp className="w-3 h-3" style={{ color: P.green }} />
      : <TrendingDown className="w-3 h-3" style={{ color: P.red }} />;
  };

  const cot = cotData?.data;
  const whale = whaleData?.data;

  if (loading && !cot && !whale) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: P.border }} />
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 rounded-xl" style={{ background: P.border }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px rgba(0,204,255,0.08), inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* Header */}
      <PanelHeader
        title="COT WHALE"
        subtitle="POSITIONING DATA"
        icon={<Fish size={22} />}
        iconColor="var(--accent-cyan)"
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        symbols={[
          { key: "NDX.INDX", label: "NASDAQ" },
          { key: "XAUUSD", label: "XAUUSD" },
          { key: "GDAXI.INDX", label: "DAX" },
          { key: "CL.COMM", label: "US Oil" },
        ]}
        activeSymbol={symbol}
        onSymbolChange={setSymbol}
        onRefresh={fetchData}
        loading={loading}
        panelId="cot-whale"
      />

      {/* COT Section */}
      {cot ? (
        <>
          {/* Percentile Gauge */}
          <div className="px-4 py-3 flex items-center gap-4" style={{ background: `${percentileColor(cot.percentile_52w)}06`, borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <div className="flex-1">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-1.5" style={{ color: P.muted }}>
                Net Non-Commercial (52W Percentile)
              </div>
              <div className="h-3 rounded-full overflow-hidden relative" style={{ background: P.border }}>
                {/* Gradient bar */}
                <div className="h-full rounded-full absolute inset-0" style={{
                  background: "linear-gradient(90deg, var(--accent-positive) 0%, var(--accent-warning) 50%, var(--accent-negative) 100%)",
                  opacity: 0.3,
                }} />
                {/* Position indicator */}
                <div className="absolute top-0 h-full w-1 rounded-full" style={{
                  left: `${Math.min(100, cot.percentile_52w || 50)}%`,
                  background: percentileColor(cot.percentile_52w),
                  boxShadow: `0 0 8px ${percentileColor(cot.percentile_52w)}`,
                  transform: "translateX(-50%)",
                }} />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[8px] font-mono" style={{ color: P.green }}>Ext. Short</span>
                <span className="text-[8px] font-mono" style={{ color: P.muted }}>Neutral</span>
                <span className="text-[8px] font-mono" style={{ color: P.red }}>Ext. Long</span>
              </div>
            </div>
            <div className="text-center px-3">
              <div className="text-xl font-bold font-mono" style={{ color: percentileColor(cot.percentile_52w), textShadow: `0 0 10px ${percentileColor(cot.percentile_52w)}40` }}>
                {cot.percentile_52w?.toFixed(0) || "—"}
              </div>
              <div className="text-[8px] font-mono" style={{ color: P.muted }}>PERCENTILE</div>
            </div>
          </div>

          {/* Extreme Warning */}
          {cot.extreme_positioning && (
            <div className="px-4 py-2">
              <div className="rounded-lg p-2 flex items-center gap-2" style={{ background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.15)" }}>
                <AlertTriangle className="w-4 h-4 shrink-0" style={{ color: P.red }} />
                <p className="text-[10px] font-mono" style={{ color: P.red }}>
                  Extreme Positioning! Reversal riski yüksek.
                </p>
              </div>
            </div>
          )}

          {/* COT Breakdown */}
          <div className="px-4 py-3 grid grid-cols-3 gap-2" style={{ borderBottom: "1px solid var(--border)" }}>
            {/* Non-Commercial (Smart Money) */}
            <div className="rounded-xl p-3" style={{ background: P.border, border: "1px solid var(--border)" }}>
              <div className="flex items-center gap-1 mb-1.5">
                <Building className="w-3 h-3" style={{ color: P.purple }} />
                <span className="text-[9px] font-mono" style={{ color: P.muted }}>Non-Comm.</span>
              </div>
              <div className="text-sm font-bold font-mono" style={{ color: netColor(cot.net_non_commercial) }}>
                {cot.net_non_commercial?.toLocaleString() || "—"}
              </div>
              <div className="flex items-center gap-1 mt-1">
                {changeArrow(cot.change_non_commercial)}
                <span className="text-[9px] font-mono" style={{ color: netColor(cot.change_non_commercial) }}>
                  {cot.change_non_commercial?.toLocaleString() || "0"}
                </span>
              </div>
            </div>

            {/* Commercial (Hedgers) */}
            <div className="rounded-xl p-3" style={{ background: P.border, border: "1px solid var(--border)" }}>
              <div className="flex items-center gap-1 mb-1.5">
                <Users className="w-3 h-3" style={{ color: P.accent }} />
                <span className="text-[9px] font-mono" style={{ color: P.muted }}>Commercial</span>
              </div>
              <div className="text-sm font-bold font-mono" style={{ color: netColor(cot.net_commercial) }}>
                {cot.net_commercial?.toLocaleString() || "—"}
              </div>
              <div className="flex items-center gap-1 mt-1">
                {changeArrow(cot.change_commercial)}
                <span className="text-[9px] font-mono" style={{ color: netColor(cot.change_commercial) }}>
                  {cot.change_commercial?.toLocaleString() || "0"}
                </span>
              </div>
            </div>

            {/* Small Specs (Dumb Money) */}
            <div className="rounded-xl p-3" style={{ background: P.border, border: "1px solid var(--border)" }}>
              <div className="flex items-center gap-1 mb-1.5">
                <User className="w-3 h-3" style={{ color: P.warn }} />
                <span className="text-[9px] font-mono" style={{ color: P.muted }}>Small Spec</span>
              </div>
              <div className="text-sm font-bold font-mono" style={{ color: netColor(cot.net_small_spec) }}>
                {cot.net_small_spec?.toLocaleString() || "—"}
              </div>
              <div className="flex items-center gap-1 mt-1">
                {changeArrow(cot.change_small_spec)}
                <span className="text-[9px] font-mono" style={{ color: netColor(cot.change_small_spec) }}>
                  {cot.change_small_spec?.toLocaleString() || "0"}
                </span>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="px-4 py-4 text-center" style={{ borderBottom: "1px solid var(--border)" }}>
          <BarChart2 className="w-8 h-8 mx-auto mb-2 opacity-30" style={{ color: P.accent }} />
          <p className="text-[10px] font-mono" style={{ color: P.muted }}>COT verisi yükleniyor...</p>
        </div>
      )}

      {/* Whale Intelligence Section */}
      {whale ? (
        <div className="px-4 py-3">
          <div className="text-[9px] uppercase tracking-widest font-mono mb-2" style={{ color: P.muted }}>
            <Fish className="w-3 h-3 inline mr-1" style={{ color: P.accent }} /> Whale Intelligence
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Smart Money Direction */}
            <div className="rounded-xl p-3" style={{ background: `${dirColor(whale.smart_money_direction)}06`, border: `1px solid ${dirColor(whale.smart_money_direction)}12` }}>
              <div className="text-[9px] font-mono mb-1" style={{ color: P.muted }}>Smart Money</div>
              <div className="text-sm font-bold font-mono" style={{ color: dirColor(whale.smart_money_direction) }}>
                {whale.smart_money_direction?.toUpperCase() || "N/A"}
              </div>
              {whale.confidence != null && (
                <div className="mt-1.5">
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: P.border }}>
                    <div className="h-full rounded-full" style={{
                      width: `${whale.confidence}%`,
                      background: dirColor(whale.smart_money_direction),
                      boxShadow: `0 0 4px ${dirColor(whale.smart_money_direction)}`,
                    }} />
                  </div>
                  <span className="text-[8px] font-mono" style={{ color: P.muted }}>{whale.confidence}%</span>
                </div>
              )}
            </div>

            {/* Institutional Bias */}
            <div className="rounded-xl p-3" style={{ background: `${dirColor(whale.institutional_bias)}06`, border: `1px solid ${dirColor(whale.institutional_bias)}12` }}>
              <div className="text-[9px] font-mono mb-1" style={{ color: P.muted }}>Institutional</div>
              <div className="text-sm font-bold font-mono" style={{ color: dirColor(whale.institutional_bias) }}>
                {whale.institutional_bias?.toUpperCase() || "N/A"}
              </div>
              <div className="flex gap-2 mt-1.5">
                {whale.whale_accumulation && (
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{ background: "var(--success-background)", color: "var(--success-text)" }}>ACCUMULATION</span>
                )}
                {whale.whale_distribution && (
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{ background: "var(--error-background)", color: "var(--error-text)" }}>DISTRIBUTION</span>
                )}
              </div>
            </div>
          </div>

          {/* Order Flow & Dark Pool */}
          <div className="flex gap-2 mt-2">
            {whale.large_order_flow && (
              <div className="flex-1 rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: P.border, border: "1px solid var(--border)" }}>
                <span className="text-[9px] font-mono" style={{ color: P.muted }}>Order Flow</span>
                <span className="text-[10px] font-bold font-mono" style={{ color: dirColor(whale.large_order_flow) }}>
                  {whale.large_order_flow?.toUpperCase()}
                </span>
              </div>
            )}
            {whale.dark_pool_activity && (
              <div className="flex-1 rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: P.border, border: "1px solid var(--border)" }}>
                <span className="text-[9px] font-mono" style={{ color: P.muted }}>Dark Pool</span>
                <span className="text-[10px] font-bold font-mono" style={{ color: dirColor(whale.dark_pool_activity) }}>
                  {whale.dark_pool_activity?.toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="px-4 py-4 text-center">
          <Fish className="w-8 h-8 mx-auto mb-2 opacity-30" style={{ color: P.accent }} />
          <p className="text-[10px] font-mono" style={{ color: P.muted }}>Whale verisi yükleniyor...</p>
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 text-center" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <p className="text-[10px] font-mono" style={{ color: P.muted }}>
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."}{" "}
          {cot?.report_date ? `| COT: ${cot.report_date}` : ""}
        </p>
      </div>
    </div>
  );
}
