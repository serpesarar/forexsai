"use client";

import { useState, useEffect } from "react";
import { PanelInfoButton } from "../PanelInfoButton";
import {
  RefreshCw,
  Shield,
  Layers,
  Target,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

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
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "NDX.INDX", label: "NASDAQ" },
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
    t?.includes("bullish") || t === "up" ? "#00ff88" : t?.includes("bearish") || t === "down" ? "#ff3366" : "#f0b429";
  const strengthBar = (s: number) => Math.min(100, (s / 10) * 100);

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-8 rounded w-1/2 mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
      </div>
    );
  }

  const bias = data?.bias;
  const accent = trendColor(bias?.direction || "neutral");

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px rgba(129,140,248,0.12), inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(129,140,248,0.2)", boxShadow: "0 0 12px rgba(129,140,248,0.3)" }}>
            <Shield className="w-4 h-4" style={{ color: "#818cf8" }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">Smart Money Concepts</h2>
            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>Order Blocks • FVG • Liquidity</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setSymbol(s.key)}
                className="px-2.5 py-1 text-[10px] font-bold font-mono transition-all"
                style={{
                  background: symbol === s.key ? "rgba(129,140,248,0.2)" : "rgba(255,255,255,0.03)",
                  color: symbol === s.key ? "#818cf8" : "rgba(255,255,255,0.4)",
                }}>
                {s.label}
              </button>
            ))}
          </div>
          <button onClick={fetchData} className="p-1.5 rounded-lg" style={{ background: "rgba(255,255,255,0.05)" }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: "rgba(255,255,255,0.35)" }} />
          </button>
          <PanelInfoButton panelId="smc-panel" />
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
          {/* Bias Banner */}
          {bias && (
            <div className="px-4 py-3 flex items-center justify-between" style={{ background: `${accent}08` }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${accent}15`, border: `1px solid ${accent}30` }}>
                  {bias.direction === "bullish" ? <TrendingUp className="w-5 h-5" style={{ color: accent }} /> :
                    bias.direction === "bearish" ? <TrendingDown className="w-5 h-5" style={{ color: accent }} /> :
                      <Activity className="w-5 h-5" style={{ color: accent }} />}
                </div>
                <div>
                  <div className="text-sm font-bold font-mono uppercase" style={{ color: accent, textShadow: `0 0 12px ${accent}40` }}>
                    {bias.direction} BIAS
                  </div>
                  <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Güven: {bias.confidence}% • İzle: {bias.key_level_to_watch?.toFixed(0)}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>İnvalidasyon</div>
                <div className="text-sm font-bold font-mono" style={{ color: "#ff3366" }}>{bias.invalidation?.toFixed(0)}</div>
              </div>
            </div>
          )}

          {/* Market Structure */}
          {data?.market_structure && (
            <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Layers className="w-3 h-3 inline mr-1" style={{ color: "#818cf8" }} /> Market Structure
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-lg p-2 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>TREND</div>
                  <div className="text-xs font-bold font-mono mt-0.5" style={{ color: trendColor(data.market_structure.current_trend) }}>
                    {data.market_structure.current_trend?.toUpperCase()}
                  </div>
                </div>
                <div className="rounded-lg p-2 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>SWING H</div>
                  <div className="text-xs font-bold font-mono mt-0.5 text-white/80">{data.market_structure.swing_high?.toFixed(0)}</div>
                </div>
                <div className="rounded-lg p-2 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>SWING L</div>
                  <div className="text-xs font-bold font-mono mt-0.5 text-white/80">{data.market_structure.swing_low?.toFixed(0)}</div>
                </div>
              </div>
              {/* BOS / CHoCH */}
              <div className="flex gap-2 mt-2">
                {data.market_structure.last_bos && (
                  <div className="flex-1 rounded-lg px-2.5 py-1.5 flex items-center justify-between" style={{ background: "rgba(0,255,136,0.06)", border: "1px solid rgba(0,255,136,0.12)" }}>
                    <span className="text-[10px] font-mono" style={{ color: "#00ff88" }}>BOS</span>
                    <span className="text-[10px] font-mono text-white/70">{data.market_structure.last_bos.direction} @ {data.market_structure.last_bos.price?.toFixed(0)}</span>
                  </div>
                )}
                {data.market_structure.last_choch && (
                  <div className="flex-1 rounded-lg px-2.5 py-1.5 flex items-center justify-between" style={{ background: "rgba(255,51,102,0.06)", border: "1px solid rgba(255,51,102,0.12)" }}>
                    <span className="text-[10px] font-mono" style={{ color: "#ff3366" }}>CHoCH</span>
                    <span className="text-[10px] font-mono text-white/70">{data.market_structure.last_choch.direction} @ {data.market_structure.last_choch.price?.toFixed(0)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Order Blocks */}
          {data?.order_blocks && data.order_blocks.length > 0 && (
            <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Target className="w-3 h-3 inline mr-1" style={{ color: "#00ccff" }} /> Order Blocks
              </h3>
              <div className="space-y-1.5">
                {data.order_blocks.slice(0, 4).map((ob, i) => {
                  const c = ob.type === "bullish" ? "#00ff88" : "#ff3366";
                  return (
                    <div key={i} className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: `${c}06`, border: `1px solid ${c}12` }}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-6 rounded-full" style={{ background: c, boxShadow: `0 0 8px ${c}50` }} />
                        <div>
                          <div className="text-[10px] font-bold font-mono" style={{ color: c }}>{ob.type.toUpperCase()} OB</div>
                          <div className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{ob.price_low?.toFixed(0)} - {ob.price_high?.toFixed(0)}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-16">
                          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                            <div className="h-full rounded-full" style={{ width: `${strengthBar(ob.strength)}%`, background: c, boxShadow: `0 0 4px ${c}` }} />
                          </div>
                          <div className="text-[8px] font-mono text-center mt-0.5" style={{ color: "rgba(255,255,255,0.25)" }}>{ob.strength}/10</div>
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
            <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Zap className="w-3 h-3 inline mr-1" style={{ color: "#f0b429" }} /> Fair Value Gaps
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {data.fair_value_gaps.slice(0, 4).map((fvg, i) => {
                  const c = fvg.direction === "bullish" ? "#00ff88" : "#ff3366";
                  return (
                    <div key={i} className="rounded-lg p-2.5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[9px] font-bold font-mono" style={{ color: c }}>{fvg.direction.toUpperCase()}</span>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{
                          background: fvg.status === "open" ? "rgba(0,255,136,0.1)" : "rgba(255,255,255,0.05)",
                          color: fvg.status === "open" ? "#00ff88" : "rgba(255,255,255,0.3)",
                        }}>{fvg.status}</span>
                      </div>
                      <div className="text-[10px] font-mono text-white/60">{fvg.low?.toFixed(0)} - {fvg.high?.toFixed(0)}</div>
                      <div className="h-1 rounded-full mt-1.5 overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                        <div className="h-full rounded-full" style={{ width: `${fvg.fill_pct || 0}%`, background: "#f0b429" }} />
                      </div>
                      <div className="text-[8px] font-mono mt-0.5" style={{ color: "rgba(255,255,255,0.2)" }}>Fill: {fvg.fill_pct || 0}%</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Liquidity Pools */}
          {data?.liquidity_pools && data.liquidity_pools.length > 0 && (
            <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>
                Liquidity Pools
              </h3>
              <div className="flex flex-wrap gap-2">
                {data.liquidity_pools.map((lp, i) => {
                  const c = lp.type === "buy_side" ? "#00ff88" : "#ff3366";
                  return (
                    <div key={i} className="rounded-lg px-3 py-1.5 flex items-center gap-2" style={{ background: `${c}06`, border: `1px solid ${c}12` }}>
                      {lp.type === "buy_side" ? <ArrowUpRight className="w-3 h-3" style={{ color: c }} /> : <ArrowDownRight className="w-3 h-3" style={{ color: c }} />}
                      <span className="text-[10px] font-mono font-bold" style={{ color: c }}>{lp.price?.toFixed(0)}</span>
                      <span className="text-[8px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>{lp.strength}</span>
                      {lp.swept && <span className="text-[8px] font-mono px-1 rounded" style={{ background: "rgba(255,51,102,0.15)", color: "#ff3366" }}>SWEPT</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Narrative */}
          {bias?.narrative && (
            <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
              <div className="rounded-xl p-3" style={{ background: "rgba(129,140,248,0.06)", border: "1px solid rgba(129,140,248,0.12)" }}>
                <p className="text-sm font-mono leading-relaxed" style={{ color: "rgba(255,255,255,0.55)" }}>{bias.narrative}</p>
              </div>
            </div>
          )}

          {/* AI Reasoning (collapsible) */}
          {data?._reasoning && (
            <div className="px-4 py-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
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
