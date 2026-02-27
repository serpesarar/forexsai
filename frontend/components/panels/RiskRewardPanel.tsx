"use client";

import { useState, useEffect } from "react";
import { PanelHeader } from "../PanelHeader";
import {
  Scale,
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

// ── Theme-aware Color Palette (CSS Variables) ───────────────────────────────
const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  textSec: "var(--text-secondary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  cyan: "var(--accent-cyan)",
  purple: "var(--accent-purple)",
};

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
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "CL.COMM", label: "US Oil" },
];

export default function RiskRewardPanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReasoning, setShowReasoning] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [symbol]);

  const generateFallbackData = (sym: string): RiskData => {
    // Static fallback data for when DeepSeek API is unavailable
    const isGold = sym === "XAUUSD";
    const isNasdaq = sym.includes("NDX") || sym.includes("NASDAQ");
    const baseRisk = isGold ? 45 : isNasdaq ? 55 : 50;
    return {
      position_sizing: {
        kelly_fraction: 0.12,
        adjusted_size: 0.08,
        reason: `DeepSeek offline — using conservative ${isGold ? 'gold' : isNasdaq ? 'equity' : 'commodity'} defaults`,
        max_risk_pct: isGold ? 1.5 : 2.0,
      },
      risk_score: {
        overall: baseRisk,
        factors: [
          "DeepSeek API unavailable — static risk estimate",
          isGold ? "Gold: moderate volatility environment assumed" : "Equity: standard market conditions assumed",
        ],
        recommendation: "Use conservative position sizing until live analysis resumes",
      },
      portfolio_heat: {
        current_exposure_pct: 0,
        max_allowed_pct: 6,
        correlation_adjustment: 1.0,
        final_heat_pct: 0,
      },
    };
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/deepseek/risk/${symbol}`);
      const json = await res.json();
      if (json.success && json.data) {
        // Check if API returned an error in data
        if (json.data.error && !json.data.risk_score) {
          // API call failed (e.g., 402 Insufficient Balance) — use fallback
          console.warn("RiskReward API error, using fallback:", json.data.error);
          setData(generateFallbackData(symbol));
        } else {
          setData(json.data);
        }
        setLastUpdate(new Date());
      } else {
        setData(generateFallbackData(symbol));
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error("Risk fetch error:", e);
      setData(generateFallbackData(symbol));
      setLastUpdate(new Date());
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
    if (!s) return P.accent;
    if (s < 30) return P.green;
    if (s < 60) return P.warn;
    return P.red;
  };

  if (loading && !data) {
    return (
      <div className="p-2 animate-pulse bg-transparent">
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: P.border }} />
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 rounded-xl" style={{ background: P.border }} />
          ))}
        </div>
      </div>
    );
  }

  const scoreColor = riskScoreColor(data?.risk_score?.overall);

  return (
    <div className="overflow-hidden bg-transparent border-0 shadow-none">
      {/* Header */}
      <PanelHeader
        title="RISK REWARD"
        subtitle="POSITION CALCULATOR"
        icon={<Scale size={24} strokeWidth={2.5} />}
        iconColor="var(--accent-cyan)"
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        symbols={SYMBOLS}
        activeSymbol={symbol}
        onSymbolChange={setSymbol}
        onRefresh={fetchData}
        loading={loading}
        panelId="risk-reward"
      />

      {data?.error ? (
        <div className="p-8 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40" style={{ color: P.warn }} />
          <p className="text-sm font-mono" style={{ color: P.muted }}>DeepSeek analiz bekleniyor...</p>
          <p className="text-[10px] mt-1 font-mono" style={{ color: P.muted }}>{data.error}</p>
        </div>
      ) : (
        <>
          {/* Risk Score + Position Sizing */}
          <div className="p-4 flex gap-3">
            {/* Risk Score */}
            {data?.risk_score && (
              <div className="flex-1 rounded-xl p-3 text-center" style={{ background: P.card, border: `1px solid ${P.border}` }}>
                <div className="relative inline-flex items-center justify-center w-20 h-20 mb-2">
                  <svg className="w-20 h-20 -rotate-90">
                    <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
                    <circle cx="40" cy="40" r="34" fill="none" stroke={scoreColor} strokeWidth="5"
                      strokeDasharray={`${((data.risk_score.overall || 0) / 100) * 213.6} 213.6`} strokeLinecap="round"
                      style={{ filter: `drop-shadow(0 0 6px ${scoreColor}60)` }} />
                  </svg>
                  <div className="absolute text-center">
                    <span className="text-lg font-bold font-mono" style={{ color: scoreColor }}>{data.risk_score.overall}</span>
                    <span className="text-[8px] font-mono block" style={{ color: P.muted }}>RISK</span>
                  </div>
                </div>
                <div className="text-[10px] font-mono" style={{ color: P.muted }}>
                  {data.risk_score.overall < 30 ? "Düşük Risk" : data.risk_score.overall < 60 ? "Orta Risk" : "Yüksek Risk"}
                </div>
              </div>
            )}

            {/* Position Sizing */}
            {data?.position_sizing && (
              <div className="flex-1 rounded-xl p-3" style={{ background: P.card, border: `1px solid ${P.border}` }}>
                <div className="text-[9px] uppercase tracking-widest font-mono mb-2" style={{ color: P.muted }}>Position Sizing</div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono" style={{ color: P.muted }}>Kelly</span>
                    <span className="text-sm font-bold font-mono" style={{ color: P.accent }}>{(data.position_sizing.kelly_fraction * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono" style={{ color: P.muted }}>Adjusted</span>
                    <span className="text-sm font-bold font-mono" style={{ color: P.green }}>{(data.position_sizing.adjusted_size * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono" style={{ color: P.muted }}>Max Risk</span>
                    <span className="text-sm font-bold font-mono" style={{ color: P.red }}>{data.position_sizing.max_risk_pct}%</span>
                  </div>
                </div>
                {data.position_sizing.reason && (
                  <div className="mt-2 text-[9px] font-mono" style={{ color: P.muted }}>{data.position_sizing.reason}</div>
                )}
              </div>
            )}
          </div>

          {/* Stop Loss & Take Profits */}
          <div className="px-4 pb-3">
            <div className="grid grid-cols-2 gap-2.5">
              {/* Stop Loss */}
              {data?.stop_loss && (
                <div className="rounded-xl p-3" style={{ background: `${P.red}10`, border: `1px solid ${P.red}20` }}>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Lock className="w-3 h-3" style={{ color: P.red }} />
                    <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: P.red }}>Stop Loss</span>
                  </div>
                  <div className="text-lg font-bold font-mono" style={{ color: P.red, textShadow: `0 0 10px ${P.red}30` }}>
                    {data.stop_loss.price?.toFixed(1)}
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[9px] font-mono" style={{ color: P.muted }}>ATR x{data.stop_loss.atr_multiplier}</span>
                    <span className="text-[9px] font-mono" style={{ color: P.muted }}>-{data.stop_loss.distance_pct?.toFixed(2)}%</span>
                  </div>
                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded mt-1 inline-block" style={{ background: `${P.red}15`, color: P.red }}>
                    {data.stop_loss.type}
                  </span>
                </div>
              )}

              {/* Trail Stop */}
              {data?.trail_stop && (
                <div className="rounded-xl p-3" style={{ background: `${P.accent}10`, border: `1px solid ${P.accent}20` }}>
                  <div className="flex items-center gap-1.5 mb-2">
                    {data.trail_stop.enabled ? <Unlock className="w-3 h-3" style={{ color: P.accent }} /> : <Lock className="w-3 h-3" style={{ color: P.muted }} />}
                    <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: P.accent }}>Trail Stop</span>
                  </div>
                  <div className="text-lg font-bold font-mono" style={{ color: P.accent, textShadow: `0 0 10px ${P.accent}30` }}>
                    {data.trail_stop.activation_price?.toFixed(1)}
                  </div>
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[9px] font-mono" style={{ color: P.muted }}>ATR x{data.trail_stop.trail_distance_atr}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{
                      background: data.trail_stop.enabled ? "var(--accent-positive-10)" : "var(--bg-hover)",
                      color: data.trail_stop.enabled ? P.green : P.muted,
                    }}>{data.trail_stop.enabled ? "AKTİF" : "PASİF"}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Take Profits */}
          {data?.take_profits && data.take_profits.length > 0 && (
            <div className="px-4 pb-3">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-2 px-1" style={{ color: P.muted }}>
                <Target className="w-3 h-3 inline mr-1" style={{ color: P.green }} /> Take Profits
              </div>
              <div className="space-y-1.5">
                {data.take_profits.map((tp, i) => (
                  <div key={i} className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: `${P.green}05`, border: `1px solid ${P.green}10` }}>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold font-mono" style={{ background: P.border }}>
                        {i + 1}
                      </div>
                      <div>
                        <div className="text-sm font-bold font-mono" style={{ color: P.green }}>{tp.level?.toFixed(1)}</div>
                        <div className="text-[9px] font-mono" style={{ color: P.muted }}>{tp.logic}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] font-bold font-mono" style={{ color: P.accent }}>%{tp.close_pct}</div>
                      <div className="text-[9px] font-mono" style={{ color: P.muted }}>R:R {tp.rr_ratio?.toFixed(1)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Portfolio Heat */}
          {data?.portfolio_heat && (
            <div className="px-4 pb-3">
              <div className="rounded-xl p-3" style={{ background: `${P.warn}05`, border: `1px solid ${P.warn}10` }}>
                <div className="flex items-center gap-1.5 mb-2">
                  <Flame className="w-3.5 h-3.5" style={{ color: P.warn }} />
                  <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: P.warn }}>Portfolio Heat</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="h-2.5 rounded-full overflow-hidden" style={{ background: P.border }}>
                      <div className="h-full rounded-full transition-all duration-700" style={{
                        width: `${Math.min(100, (data.portfolio_heat.final_heat_pct / data.portfolio_heat.max_allowed_pct) * 100)}%`,
                        background: data.portfolio_heat.final_heat_pct > data.portfolio_heat.max_allowed_pct * 0.8
                          ? `${P.red}30`
                          : `${P.green}30`,
                        boxShadow: `0 0 8px ${P.green}30`,
                      }} />
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-[9px] font-mono" style={{ color: P.muted }}>0%</span>
                      <span className="text-[9px] font-mono" style={{ color: P.muted }}>{data.portfolio_heat.max_allowed_pct}%</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold font-mono" style={{ color: P.warn }}>{data.portfolio_heat.final_heat_pct?.toFixed(1)}%</div>
                    <div className="text-[8px] font-mono" style={{ color: P.muted }}>Korrelasyon: x{data.portfolio_heat.correlation_adjustment}</div>
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
                  <div key={i} className="flex items-center gap-1.5 text-[10px] font-mono" style={{ color: P.muted }}>
                    <AlertTriangle className="w-3 h-3 shrink-0" style={{ color: P.warn }} /> {f}
                  </div>
                ))}
              </div>
              {data.risk_score.recommendation && (
                <div className="mt-2 rounded-lg p-2.5" style={{ background: `${P.accent}05`, border: `1px solid ${P.accent}10` }}>
                  <p className="text-[10px] font-mono" style={{ color: P.accent }}>{data.risk_score.recommendation}</p>
                </div>
              )}
            </div>
          )}

          {/* AI Reasoning */}
          {data?._reasoning && (
            <div className="px-4 pb-2">
              <button onClick={() => setShowReasoning(!showReasoning)} className="flex items-center gap-1.5 text-[10px] font-mono w-full" style={{ color: P.muted }}>
                {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                AI Reasoning
              </button>
              {showReasoning && (
                <div className="mt-2 rounded-lg p-3 text-[10px] font-mono leading-relaxed whitespace-pre-wrap" style={{ background: P.surface, color: P.muted, maxHeight: 200, overflowY: "auto" }}>
                  {data._reasoning}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="px-2 py-2 text-center bg-transparent">
        <p className="text-[10px] font-mono" style={{ color: P.muted }}>
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."} | DeepSeek-R1
        </p>
      </div>
    </div>
  );
}
