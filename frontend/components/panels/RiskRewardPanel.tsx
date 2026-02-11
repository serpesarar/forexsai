"use client";

import { useState, useEffect } from "react";
import {
  RefreshCw,
  Shield,
  Target,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Percent,
  ChevronDown,
  ChevronUp,
  Flame,
  Lock,
  Unlock,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface RiskData {
  position_sizing?: {
    kelly_fraction: number;
    adjusted_size: number;
    reason: string;
    max_risk_pct: number;
  };
  stop_loss?: {
    price: number;
    atr_multiplier: number;
    type: string;
    distance_pct: number;
  };
  take_profits?: Array<{
    level: number;
    close_pct: number;
    rr_ratio: number;
    logic: string;
  }>;
  trail_stop?: {
    activation_price: number;
    trail_distance_atr: number;
    enabled: boolean;
  };
  portfolio_heat?: {
    current_exposure_pct: number;
    max_allowed_pct: number;
    correlation_adjustment: number;
    final_heat_pct: number;
  };
  risk_score?: {
    overall: number;
    factors: string[];
    recommendation: string;
  };
  _reasoning?: string;
  error?: string;
}

const SYMBOLS = [
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "NDX.INDX", label: "NASDAQ" },
];

export default function RiskRewardPanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReasoning, setShowReasoning] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/deepseek/risk/${symbol}`);
      const json = await res.json();
      if (json.success && json.data) {
        setData(json.data);
        setLastUpdate(new Date());
      } else {
        setData({ error: json.error || "No data" });
      }
    } catch (e) {
      console.error("Risk fetch error:", e);
      setData({ error: "Connection failed" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1800000); // 30 min - DeepSeek analysis doesn't change frequently
    return () => clearInterval(interval);
  }, [symbol]);

  const riskScoreColor = (s?: number) => {
    if (!s) return "#818cf8";
    if (s < 30) return "#00ff88";
    if (s < 60) return "#f0b429";
    return "#ff3366";
  };

  if (loading && !data) {
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

  const scoreColor = riskScoreColor(data?.risk_score?.overall);

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px rgba(0,255,136,0.10), inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(0,255,136,0.2)", boxShadow: "0 0 12px rgba(0,255,136,0.3)" }}>
            <Shield className="w-4 h-4" style={{ color: "#00ff88" }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">Risk / Reward Optimizer</h2>
            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>Kelly Criterion • Position Sizing</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setSymbol(s.key)}
                className="px-2.5 py-1 text-[10px] font-bold font-mono transition-all"
                style={{
                  background: symbol === s.key ? "rgba(0,255,136,0.2)" : "rgba(255,255,255,0.03)",
                  color: symbol === s.key ? "#00ff88" : "rgba(255,255,255,0.4)",
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

      {data?.error ? (
        <div className="p-8 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40" style={{ color: "#f0b429" }} />
          <p className="text-sm font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>DeepSeek analiz bekleniyor...</p>
          <p className="text-[10px] mt-1 font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>{data.error}</p>
        </div>
      ) : (
        <>
          {/* Risk Score + Position Sizing */}
          <div className="p-4 flex gap-3">
            {/* Risk Score */}
            {data?.risk_score && (
              <div className="flex-1 rounded-xl p-3 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div className="relative inline-flex items-center justify-center w-20 h-20 mb-2">
                  <svg className="w-20 h-20 -rotate-90">
                    <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
                    <circle cx="40" cy="40" r="34" fill="none" stroke={scoreColor} strokeWidth="5"
                      strokeDasharray={`${((data.risk_score.overall || 0) / 100) * 213.6} 213.6`} strokeLinecap="round"
                      style={{ filter: `drop-shadow(0 0 6px ${scoreColor}60)` }} />
                  </svg>
                  <div className="absolute text-center">
                    <span className="text-lg font-bold font-mono" style={{ color: scoreColor }}>{data.risk_score.overall}</span>
                    <span className="text-[8px] font-mono block" style={{ color: "rgba(255,255,255,0.2)" }}>RISK</span>
                  </div>
                </div>
                <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>
                  {data.risk_score.overall < 30 ? "Düşük Risk" : data.risk_score.overall < 60 ? "Orta Risk" : "Yüksek Risk"}
                </div>
              </div>
            )}

            {/* Position Sizing */}
            {data?.position_sizing && (
              <div className="flex-1 rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div className="text-[9px] uppercase tracking-widest font-mono mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>Position Sizing</div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>Kelly</span>
                    <span className="text-sm font-bold font-mono" style={{ color: "#00ccff" }}>{(data.position_sizing.kelly_fraction * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>Adjusted</span>
                    <span className="text-sm font-bold font-mono" style={{ color: "#00ff88" }}>{(data.position_sizing.adjusted_size * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>Max Risk</span>
                    <span className="text-sm font-bold font-mono" style={{ color: "#ff3366" }}>{data.position_sizing.max_risk_pct}%</span>
                  </div>
                </div>
                {data.position_sizing.reason && (
                  <div className="mt-2 text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>{data.position_sizing.reason}</div>
                )}
              </div>
            )}
          </div>

          {/* Stop Loss & Take Profits */}
          <div className="px-4 pb-3">
            <div className="grid grid-cols-2 gap-2.5">
              {/* Stop Loss */}
              {data?.stop_loss && (
                <div className="rounded-xl p-3" style={{ background: "rgba(255,51,102,0.06)", border: "1px solid rgba(255,51,102,0.12)" }}>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Lock className="w-3 h-3" style={{ color: "#ff3366" }} />
                    <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: "#ff3366" }}>Stop Loss</span>
                  </div>
                  <div className="text-lg font-bold font-mono" style={{ color: "#ff3366", textShadow: "0 0 10px rgba(255,51,102,0.3)" }}>
                    {data.stop_loss.price?.toFixed(1)}
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>ATR x{data.stop_loss.atr_multiplier}</span>
                    <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>-{data.stop_loss.distance_pct?.toFixed(2)}%</span>
                  </div>
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded mt-1 inline-block" style={{ background: "rgba(255,51,102,0.15)", color: "#ff3366" }}>
                    {data.stop_loss.type}
                  </span>
                </div>
              )}

              {/* Trail Stop */}
              {data?.trail_stop && (
                <div className="rounded-xl p-3" style={{ background: "rgba(0,204,255,0.06)", border: "1px solid rgba(0,204,255,0.12)" }}>
                  <div className="flex items-center gap-1.5 mb-2">
                    {data.trail_stop.enabled ? <Unlock className="w-3 h-3" style={{ color: "#00ccff" }} /> : <Lock className="w-3 h-3" style={{ color: "rgba(255,255,255,0.3)" }} />}
                    <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: "#00ccff" }}>Trail Stop</span>
                  </div>
                  <div className="text-lg font-bold font-mono" style={{ color: "#00ccff", textShadow: "0 0 10px rgba(0,204,255,0.3)" }}>
                    {data.trail_stop.activation_price?.toFixed(1)}
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>ATR x{data.trail_stop.trail_distance_atr}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{
                      background: data.trail_stop.enabled ? "rgba(0,255,136,0.1)" : "rgba(255,255,255,0.05)",
                      color: data.trail_stop.enabled ? "#00ff88" : "rgba(255,255,255,0.3)",
                    }}>{data.trail_stop.enabled ? "AKTİF" : "PASİF"}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Take Profits */}
          {data?.take_profits && data.take_profits.length > 0 && (
            <div className="px-4 pb-3">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-2 px-1" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Target className="w-3 h-3 inline mr-1" style={{ color: "#00ff88" }} /> Take Profits
              </div>
              <div className="space-y-1.5">
                {data.take_profits.map((tp, i) => (
                  <div key={i} className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.08)" }}>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold font-mono" style={{ background: "rgba(0,255,136,0.15)", color: "#00ff88" }}>
                        {i + 1}
                      </div>
                      <div>
                        <div className="text-sm font-bold font-mono" style={{ color: "#00ff88" }}>{tp.level?.toFixed(1)}</div>
                        <div className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>{tp.logic}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] font-bold font-mono" style={{ color: "#00ccff" }}>%{tp.close_pct}</div>
                      <div className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>R:R {tp.rr_ratio?.toFixed(1)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Portfolio Heat */}
          {data?.portfolio_heat && (
            <div className="px-4 pb-3">
              <div className="rounded-xl p-3" style={{ background: "rgba(240,180,41,0.06)", border: "1px solid rgba(240,180,41,0.12)" }}>
                <div className="flex items-center gap-1.5 mb-2">
                  <Flame className="w-3.5 h-3.5" style={{ color: "#f0b429" }} />
                  <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: "#f0b429" }}>Portfolio Heat</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="h-2.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                      <div className="h-full rounded-full transition-all duration-700" style={{
                        width: `${Math.min(100, (data.portfolio_heat.final_heat_pct / data.portfolio_heat.max_allowed_pct) * 100)}%`,
                        background: data.portfolio_heat.final_heat_pct > data.portfolio_heat.max_allowed_pct * 0.8
                          ? "linear-gradient(90deg, #f0b429, #ff3366)"
                          : "linear-gradient(90deg, #00ff8880, #00ff88)",
                        boxShadow: "0 0 8px rgba(0,255,136,0.3)",
                      }} />
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>0%</span>
                      <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>{data.portfolio_heat.max_allowed_pct}%</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold font-mono" style={{ color: "#f0b429" }}>{data.portfolio_heat.final_heat_pct?.toFixed(1)}%</div>
                    <div className="text-[8px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>Korrelasyon: x{data.portfolio_heat.correlation_adjustment}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Risk Factors */}
          {data?.risk_score?.factors && data.risk_score.factors.length > 0 && (
            <div className="px-4 pb-3">
              <div className="space-y-1">
                {data.risk_score.factors.map((f, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.35)" }}>
                    <AlertTriangle className="w-3 h-3 shrink-0" style={{ color: "#f0b429" }} /> {f}
                  </div>
                ))}
              </div>
              {data.risk_score.recommendation && (
                <div className="mt-2 rounded-lg p-2.5" style={{ background: "rgba(129,140,248,0.06)", border: "1px solid rgba(129,140,248,0.1)" }}>
                  <p className="text-[10px] font-mono" style={{ color: "#818cf8" }}>{data.risk_score.recommendation}</p>
                </div>
              )}
            </div>
          )}

          {/* AI Reasoning */}
          {data?._reasoning && (
            <div className="px-4 pb-2">
              <button onClick={() => setShowReasoning(!showReasoning)} className="flex items-center gap-1.5 text-[10px] font-mono w-full" style={{ color: "rgba(255,255,255,0.3)" }}>
                {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                AI Reasoning
              </button>
              {showReasoning && (
                <div className="mt-2 rounded-lg p-3 text-[10px] font-mono leading-relaxed whitespace-pre-wrap" style={{ background: "rgba(0,0,0,0.3)", color: "rgba(255,255,255,0.35)", maxHeight: 200, overflowY: "auto" }}>
                  {data._reasoning}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="px-4 py-2 text-center" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <p className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."} | DeepSeek-R1
        </p>
      </div>
    </div>
  );
}
