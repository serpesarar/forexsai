"use client";

import { useState, useEffect } from "react";
import { PanelHeader } from "../PanelHeader";
import {
  TrendingUp,
  SecurityShieldIcon as Shield,
  AnalysisIcon as Layers,
  TargetIcon as Target,
  ArrowDownIcon as TrendingDown,
  ActivityIcon as Activity,
  AlertIcon as AlertTriangle,
  ZapIcon as Zap,
  ArrowUpRightIcon as ArrowUpRight,
  ArrowDownRightIcon as ArrowDownRight,
  MinusIcon as Minus,
  ChevronDownIcon as ChevronDown,
  ChevronUpIcon as ChevronUp,
} from "../ui/CustomIcons";

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
const P = { bg: "var(--bg-primary)", card: "var(--bg-card)", surface: "var(--bg-surface)", border: "var(--border-subtle)", text: "var(--text-primary)", muted: "var(--text-muted)", green: "var(--accent-positive)", red: "var(--accent-negative)", warn: "var(--accent-warning)", accent: "var(--accent-info)" };

interface SMCData {
  market_structure?: {
    current_trend: string;
    last_bos?: { direction: string; price: number; confirmed: boolean };
    last_choch?: { direction: string; price: number; confirmed: boolean };
    swing_high: number;
    swing_low: number;
  };
  order_blocks?: Array<{
    type: string;
    price_high: number;
    price_low: number;
    strength: number;
    status: string;
    timeframe?: string;
  }>;
  fair_value_gaps?: Array<{
    direction: string;
    high: number;
    low: number;
    fill_pct: number;
    status: string;
  }>;
  liquidity_pools?: Array<{
    type: string;
    price: number;
    strength: string;
    swept: boolean;
  }>;
  breaker_blocks?: Array<{
    type: string;
    price_high: number;
    price_low: number;
    status: string;
  }>;
  bias?: {
    direction: string;
    confidence: number;
    key_level_to_watch: number;
    invalidation: number;
    narrative: string;
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

export default function SMCPanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [data, setData] = useState<SMCData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReasoning, setShowReasoning] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [symbol]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/deepseek/smc/${symbol}`);
      const json = await res.json();
      if (json.success && json.data) {
        setData(json.data);
        setLastUpdate(new Date());
      } else {
        setData({ error: json.error || "No data" });
      }
    } catch (e) {
      console.error("SMC fetch error:", e);
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

  const trendColor = (t: string) =>
    t?.includes("bullish") || t === "up" ? "var(--accent-positive)" : t?.includes("bearish") || t === "down" ? "var(--accent-negative)" : "var(--accent-warning)";
  const strengthBar = (s: number) => Math.min(100, (s / 10) * 100);

  if (loading && !data) {
    return (
      <div className="p-2 animate-pulse bg-transparent">
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: "var(--bg-input)" }} />
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl" style={{ background: "var(--bg-input)" }} />
          ))}
        </div>
      </div>
    );
  }

  const bias = data?.bias;
  const accent = trendColor(bias?.direction || "neutral");

  return (
    <div className="overflow-hidden bg-transparent shadow-none border-0">

      <PanelHeader
        title="SMC"
        subtitle="SMART MONEY CONCEPTS"
        icon={<TrendingUp size={22} />}
        iconColor="var(--accent-cyan)"
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        symbols={SYMBOLS}
        activeSymbol={symbol}
        onSymbolChange={setSymbol}
        onRefresh={fetchData}
        loading={loading}
        panelId="smc"
      />

      {data?.error ? (
        <div className="p-8 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40" style={{ color: "var(--accent-warning)" }} />
          <p className="text-sm font-mono" style={{ color: "var(--text-muted)" }}>DeepSeek analiz bekleniyor...</p>
          <p className="text-[10px] mt-1 font-mono" style={{ color: "var(--text-disabled)" }}>{data.error}</p>
        </div>
      ) : (
        <>
          {/* Bias Banner */}
          {bias && (
            <div className="px-4 py-3 flex items-center justify-between" style={{ background: "var(--info-bg)" }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--info-bg)", border: "1px solid var(--info-border)" }}>
                  {bias.direction === "bullish" ? <TrendingUp className="w-5 h-5" style={{ color: accent }} /> :
                    bias.direction === "bearish" ? <TrendingDown className="w-5 h-5" style={{ color: accent }} /> :
                      <Activity className="w-5 h-5" style={{ color: accent }} />}
                </div>
                <div>
                  <div className="text-sm font-bold font-mono uppercase" style={{ fontFamily: FONT, color: accent }}>
                    {bias.direction} BIAS
                  </div>
                  <div style={{ fontFamily: FONT, fontSize: 10, color: "var(--text-muted)" }}>
                    Güven: {bias.confidence}% • İzle: {bias.key_level_to_watch?.toFixed(0)}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>İnvalidasyon</div>
                <div style={{ fontFamily: FONT, fontSize: 14, fontWeight: 700, color: "var(--accent-negative)" }}>{bias.invalidation?.toFixed(0)}</div>
              </div>
            </div>
          )}

          {/* Market Structure */}
          {data?.market_structure && (
            <div className="px-2 py-2 border-0">
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: P.muted }}>
                <Layers className="w-3 h-3 inline mr-1" style={{ color: P.accent }} /> Market Structure
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-lg p-2 text-center" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                  <div className="text-[9px] font-mono" style={{ color: P.muted }}>TREND</div>
                  <div className="text-xs font-bold font-mono mt-0.5" style={{ color: trendColor(data.market_structure.current_trend) }}>
                    {data.market_structure.current_trend?.toUpperCase()}
                  </div>
                </div>
                <div className="rounded-lg p-2 text-center" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                  <div className="text-[9px] font-mono" style={{ color: P.muted }}>SWING H</div>
                  <div className="text-xs font-bold font-mono mt-0.5 text-white/80">{data.market_structure.swing_high?.toFixed(0)}</div>
                </div>
                <div className="rounded-lg p-2 text-center" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                  <div className="text-[9px] font-mono" style={{ color: P.muted }}>SWING L</div>
                  <div className="text-xs font-bold font-mono mt-0.5 text-white/80">{data.market_structure.swing_low?.toFixed(0)}</div>
                </div>
              </div>
              {/* BOS / CHoCH */}
              <div className="flex gap-2 mt-2">
                {data.market_structure.last_bos && (
                  <div className="flex-1 rounded-lg px-2.5 py-1.5 flex items-center justify-between" style={{ background: "var(--success-bg)", border: "1px solid var(--success-border)" }}>
                    <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, color: "var(--accent-positive)" }}>BOS</span>
                    <span className="text-[10px] font-mono text-white/70">{data.market_structure.last_bos.direction} @ {data.market_structure.last_bos.price?.toFixed(0)}</span>
                  </div>
                )}
                {data.market_structure.last_choch && (
                  <div className="flex-1 rounded-lg px-2.5 py-1.5 flex items-center justify-between" style={{ background: "var(--danger-bg)", border: "1px solid var(--danger-border)" }}>
                    <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, color: "var(--accent-negative)" }}>CHoCH</span>
                    <span className="text-[10px] font-mono text-white/70">{data.market_structure.last_choch.direction} @ {data.market_structure.last_choch.price?.toFixed(0)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Order Blocks */}
          {data?.order_blocks && data.order_blocks.length > 0 && (
            <div className="px-2 py-2 border-0">
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: P.muted }}>
                <Target className="w-3 h-3 inline mr-1" style={{ color: P.accent }} /> Order Blocks
              </h3>
              <div className="space-y-1.5">
                {data.order_blocks.slice(0, 4).map((ob, i) => {
                  const c = ob.type === "bullish" ? "var(--accent-positive)" : "var(--accent-negative)";
                  return (
                    <div key={i} className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: `${c}10`, border: `1px solid ${c}20` }}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-6 rounded-full" style={{ background: c }} />
                        <div>
                          <div className="text-[10px] font-bold font-mono" style={{ color: c }}>{ob.type.toUpperCase()} OB</div>
                          <div className="text-[9px] font-mono" style={{ color: P.muted }}>{ob.price_low?.toFixed(0)} - {ob.price_high?.toFixed(0)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-16">
                          <div className="rounded-full overflow-hidden" style={{ height: 4, background: "var(--border-subtle)" }}>
                            <div className="h-full rounded-full" style={{ width: `${strengthBar(ob.strength)}%`, background: c, opacity: 0.85 }} />
                          </div>
                          <div className="text-[8px] font-mono text-center mt-0.5" style={{ color: P.muted }}>{ob.strength}/10</div>
                        </div>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${c}15`, color: c }}>{ob.status}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Fair Value Gaps */}
          {data?.fair_value_gaps && data.fair_value_gaps.length > 0 && (
            <div className="px-2 py-2 border-0">
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: P.muted }}>
                <Zap className="w-3 h-3 inline mr-1" style={{ color: P.warn }} /> Fair Value Gaps
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {data.fair_value_gaps.slice(0, 4).map((fvg, i) => {
                  const c = fvg.direction === "bullish" ? "var(--accent-positive)" : "var(--accent-negative)";
                  return (
                    <div key={i} className="rounded-lg p-2.5" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[9px] font-bold font-mono" style={{ color: c }}>{fvg.direction.toUpperCase()}</span>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{
                          background: fvg.status === "open" ? "var(--success-bg)" : "var(--bg-hover)",
                          color: fvg.status === "open" ? "var(--accent-positive)" : P.muted,
                        }}>{fvg.status}</span>
                      </div>
                      <div className="text-[10px] font-mono text-white/60">{fvg.low?.toFixed(0)} - {fvg.high?.toFixed(0)}</div>
                      <div className="rounded-full mt-1.5 overflow-hidden" style={{ height: 4, background: "var(--border-subtle)" }}>
                        <div className="h-full rounded-full" style={{ width: `${fvg.fill_pct || 0}%`, background: "var(--accent-warning)", opacity: 0.85 }} />
                      </div>
                      <div className="text-[8px] font-mono mt-0.5" style={{ color: P.muted }}>Fill: {fvg.fill_pct || 0}%</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Liquidity Pools */}
          {data?.liquidity_pools && data.liquidity_pools.length > 0 && (
            <div className="px-2 py-2 border-0">
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: P.muted }}>
                Liquidity Pools
              </h3>
              <div className="flex flex-wrap gap-2">
                {data.liquidity_pools.map((lp, i) => {
                  const c = lp.type === "buy_side" ? "var(--accent-positive)" : "var(--accent-negative)";
                  return (
                    <div key={i} className="rounded-lg px-3 py-1.5 flex items-center gap-2" style={{ background: `${c}10`, border: `1px solid ${c}20` }}>
                      {lp.type === "buy_side" ? <ArrowUpRight className="w-3 h-3" style={{ color: c }} /> : <ArrowDownRight className="w-3 h-3" style={{ color: c }} />}
                      <span className="text-[10px] font-mono font-bold" style={{ color: c }}>{lp.price?.toFixed(0)}</span>
                      <span className="text-[8px] font-mono" style={{ color: P.muted }}>{lp.strength}</span>
                      {lp.swept && <span className="text-[8px] font-mono px-1 rounded" style={{ background: "var(--danger-bg)", color: "var(--accent-negative)" }}>SWEPT</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Narrative */}
          {bias?.narrative && (
            <div className="px-2 py-2 border-0">
              <div className="rounded-xl p-3" style={{ background: "var(--info-bg)", border: "1px solid var(--info-border)" }}>
                <p style={{ fontFamily: FONT, fontSize: 12, lineHeight: 1.6, color: P.text }}>{bias.narrative}</p>
              </div>
            </div>
          )}

          {/* AI Reasoning (collapsible) */}
          {data?._reasoning && (
            <div className="px-2 py-2 border-0">
              <button onClick={() => setShowReasoning(!showReasoning)} className="flex items-center gap-1.5 text-[10px] font-mono w-full" style={{ color: P.muted }}>
                {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                AI Reasoning
              </button>
              {showReasoning && (
                <div className="mt-2 rounded-lg p-3 text-[10px] font-mono leading-relaxed whitespace-pre-wrap" style={{ background: "var(--bg-surface)", color: P.muted, maxHeight: 200, overflowY: "auto" }}>
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
