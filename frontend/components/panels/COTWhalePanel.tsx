"use client";

import { useState, useEffect } from "react";
import {
  RefreshCw,
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
    if (!d) return "rgba(255,255,255,0.4)";
    const l = d.toLowerCase();
    if (l.includes("bull") || l.includes("buy") || l.includes("long") || l.includes("accumul")) return "#00ff88";
    if (l.includes("bear") || l.includes("sell") || l.includes("short") || l.includes("distrib")) return "#ff3366";
    return "#f0b429";
  };

  const percentileColor = (p?: number) => {
    if (!p) return "#818cf8";
    if (p > 80) return "#ff3366";
    if (p < 20) return "#00ff88";
    return "#f0b429";
  };

  const netColor = (n?: number) => {
    if (!n) return "rgba(255,255,255,0.4)";
    return n > 0 ? "#00ff88" : "#ff3366";
  };

  const changeArrow = (c?: number) => {
    if (!c) return null;
    return c > 0
      ? <TrendingUp className="w-3 h-3" style={{ color: "#00ff88" }} />
      : <TrendingDown className="w-3 h-3" style={{ color: "#ff3366" }} />;
  };

  const cot = cotData?.data;
  const whale = whaleData?.data;

  if (loading && !cot && !whale) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px rgba(0,204,255,0.08), inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(0,204,255,0.2)", boxShadow: "0 0 12px rgba(0,204,255,0.3)" }}>
            <Fish className="w-4 h-4" style={{ color: "#00ccff" }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">COT & Whale Intelligence</h2>
            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>Kurumsal Pozisyon Takibi</p>
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
        </div>
      </div>

      {/* COT Section */}
      {cot ? (
        <>
          {/* Percentile Gauge */}
          <div className="px-4 py-3 flex items-center gap-4" style={{ background: `${percentileColor(cot.percentile_52w)}06`, borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <div className="flex-1">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                Net Non-Commercial (52W Percentile)
              </div>
              <div className="h-3 rounded-full overflow-hidden relative" style={{ background: "rgba(255,255,255,0.06)" }}>
                {/* Gradient bar */}
                <div className="h-full rounded-full absolute inset-0" style={{
                  background: "linear-gradient(90deg, #00ff88 0%, #f0b429 50%, #ff3366 100%)",
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
                <span className="text-[8px] font-mono" style={{ color: "#00ff88" }}>Ext. Short</span>
                <span className="text-[8px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>Neutral</span>
                <span className="text-[8px] font-mono" style={{ color: "#ff3366" }}>Ext. Long</span>
              </div>
            </div>
            <div className="text-center px-3">
              <div className="text-xl font-bold font-mono" style={{ color: percentileColor(cot.percentile_52w), textShadow: `0 0 10px ${percentileColor(cot.percentile_52w)}40` }}>
                {cot.percentile_52w?.toFixed(0) || "—"}
              </div>
              <div className="text-[8px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>PERCENTILE</div>
            </div>
          </div>

          {/* Extreme Warning */}
          {cot.extreme_positioning && (
            <div className="px-4 py-2">
              <div className="rounded-lg p-2 flex items-center gap-2" style={{ background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.15)" }}>
                <AlertTriangle className="w-4 h-4 shrink-0" style={{ color: "#ff3366" }} />
                <p className="text-[10px] font-mono" style={{ color: "#ff3366" }}>
                  Extreme Positioning! Reversal riski yüksek.
                </p>
              </div>
            </div>
          )}

          {/* COT Breakdown */}
          <div className="px-4 py-3 grid grid-cols-3 gap-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            {/* Non-Commercial (Smart Money) */}
            <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div className="flex items-center gap-1 mb-1.5">
                <Building className="w-3 h-3" style={{ color: "#818cf8" }} />
                <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Non-Comm.</span>
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
            <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div className="flex items-center gap-1 mb-1.5">
                <Users className="w-3 h-3" style={{ color: "#00ccff" }} />
                <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Commercial</span>
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
            <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div className="flex items-center gap-1 mb-1.5">
                <User className="w-3 h-3" style={{ color: "#f0b429" }} />
                <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Small Spec</span>
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
        <div className="px-4 py-4 text-center" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
          <BarChart2 className="w-8 h-8 mx-auto mb-2 opacity-30" style={{ color: "#00ccff" }} />
          <p className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>COT verisi yükleniyor...</p>
        </div>
      )}

      {/* Whale Intelligence Section */}
      {whale ? (
        <div className="px-4 py-3">
          <div className="text-[9px] uppercase tracking-widest font-mono mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
            <Fish className="w-3 h-3 inline mr-1" style={{ color: "#00ccff" }} /> Whale Intelligence
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Smart Money Direction */}
            <div className="rounded-xl p-3" style={{ background: `${dirColor(whale.smart_money_direction)}06`, border: `1px solid ${dirColor(whale.smart_money_direction)}12` }}>
              <div className="text-[9px] font-mono mb-1" style={{ color: "rgba(255,255,255,0.3)" }}>Smart Money</div>
              <div className="text-sm font-bold font-mono" style={{ color: dirColor(whale.smart_money_direction) }}>
                {whale.smart_money_direction?.toUpperCase() || "N/A"}
              </div>
              {whale.confidence != null && (
                <div className="mt-1.5">
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                    <div className="h-full rounded-full" style={{
                      width: `${whale.confidence}%`,
                      background: dirColor(whale.smart_money_direction),
                      boxShadow: `0 0 4px ${dirColor(whale.smart_money_direction)}`,
                    }} />
                  </div>
                  <span className="text-[8px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>{whale.confidence}%</span>
                </div>
              )}
            </div>

            {/* Institutional Bias */}
            <div className="rounded-xl p-3" style={{ background: `${dirColor(whale.institutional_bias)}06`, border: `1px solid ${dirColor(whale.institutional_bias)}12` }}>
              <div className="text-[9px] font-mono mb-1" style={{ color: "rgba(255,255,255,0.3)" }}>Institutional</div>
              <div className="text-sm font-bold font-mono" style={{ color: dirColor(whale.institutional_bias) }}>
                {whale.institutional_bias?.toUpperCase() || "N/A"}
              </div>
              <div className="flex gap-2 mt-1.5">
                {whale.whale_accumulation && (
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88" }}>ACCUMULATION</span>
                )}
                {whale.whale_distribution && (
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{ background: "rgba(255,51,102,0.1)", color: "#ff3366" }}>DISTRIBUTION</span>
                )}
              </div>
            </div>
          </div>

          {/* Order Flow & Dark Pool */}
          <div className="flex gap-2 mt-2">
            {whale.large_order_flow && (
              <div className="flex-1 rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Order Flow</span>
                <span className="text-[10px] font-bold font-mono" style={{ color: dirColor(whale.large_order_flow) }}>
                  {whale.large_order_flow?.toUpperCase()}
                </span>
              </div>
            )}
            {whale.dark_pool_activity && (
              <div className="flex-1 rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Dark Pool</span>
                <span className="text-[10px] font-bold font-mono" style={{ color: dirColor(whale.dark_pool_activity) }}>
                  {whale.dark_pool_activity?.toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="px-4 py-4 text-center">
          <Fish className="w-8 h-8 mx-auto mb-2 opacity-30" style={{ color: "#00ccff" }} />
          <p className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Whale verisi yükleniyor...</p>
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 text-center" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <p className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."}{" "}
          {cot?.report_date ? `| COT: ${cot.report_date}` : ""}
        </p>
      </div>
    </div>
  );
}
