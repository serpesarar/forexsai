"use client";

import { useState, useEffect } from "react";
import { PanelInfoButton } from "../PanelInfoButton";
import {
  RefreshCw,
  Calendar,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Sun,
  Moon,
  Globe,
  Zap,
  ChevronDown,
  ChevronUp,
  Clock,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface SeasonalityData {
  monthly_stats?: {
    month: string;
    historical_win_rate: number;
    avg_return_pct: number;
    best_year?: { year: number; return_pct: number };
    worst_year?: { year: number; return_pct: number };
    current_performance: string;
  };
  day_of_week?: {
    day: string;
    historical_bias: string;
    win_rate: number;
    avg_range_pct: number;
  };
  session_analysis?: {
    asian: { bias: string; avg_range: number };
    london: { bias: string; avg_range: number };
    new_york: { bias: string; avg_range: number };
    gap_fill_rate_pct: number;
  };
  upcoming_events?: Array<{
    event: string;
    impact: string;
    expected_volatility_pct: number;
    direction_bias: string;
  }>;
  anomalies?: Array<{
    type: string;
    description: string;
    significance: string;
  }>;
  seasonal_edge?: {
    direction: string;
    confidence: number;
    summary: string;
  };
  _reasoning?: string;
  error?: string;
}

const SYMBOLS = [
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "NDX.INDX", label: "NASDAQ" },
];

export default function SeasonalityPanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [data, setData] = useState<SeasonalityData | null>(null);
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
      const res = await fetch(`${API_BASE}/api/deepseek/seasonality/${symbol}`);
      const json = await res.json();
      if (json.success && json.data) {
        setData(json.data);
        setLastUpdate(new Date());
      } else {
        setData({ error: json.error || "No data" });
      }
    } catch (e) {
      console.error("Seasonality fetch error:", e);
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

  const biasColor = (b?: string) => {
    if (!b) return "rgba(255,255,255,0.4)";
    const l = b.toLowerCase();
    if (l.includes("bull")) return "#00ff88";
    if (l.includes("bear")) return "#ff3366";
    return "#f0b429";
  };

  const impactColor = (i?: string) => {
    if (i === "high") return "#ff3366";
    if (i === "medium") return "#f0b429";
    return "#00ccff";
  };

  const sigColor = (s?: string) => {
    if (s === "high") return "#ff3366";
    if (s === "medium") return "#f0b429";
    return "#00ccff";
  };

  const sessionIcon = (s: string) => {
    if (s === "asian") return <Moon className="w-3.5 h-3.5" style={{ color: "#818cf8" }} />;
    if (s === "london") return <Globe className="w-3.5 h-3.5" style={{ color: "#00ccff" }} />;
    return <Sun className="w-3.5 h-3.5" style={{ color: "#f0b429" }} />;
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

  const edge = data?.seasonal_edge;
  const edgeColor = biasColor(edge?.direction);

  return (
    <div className="glass-premium rounded-2xl overflow-hidden">

      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between border-b border-white/5 bg-black/20">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-amber-500/20 shadow-[0_0_12px_rgba(240,180,41,0.3)]">
            <Calendar className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">Seasonality & Anomaly</h2>
            <p className="text-[10px] text-white/30">Tarihsel İstatistik & Anomali Tespiti</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex rounded-lg overflow-hidden border border-white/10">
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setSymbol(s.key)}
                className={`px-2.5 py-1 text-[10px] font-bold font-mono transition-all ${symbol === s.key
                  ? "bg-amber-500/20 text-amber-400"
                  : "bg-white/5 text-white/40 hover:bg-white/10"
                  }`}
              >
                {s.label}
              </button>
            ))}
          </div>
          <button onClick={fetchData} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""} text-white/40`} />
          </button>
          <PanelInfoButton panelId="seasonality" />
        </div>
      </div>

      {data?.error ? (
        <div className="p-8 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40 text-amber-500" />
          <p className="text-sm font-mono text-white/40">DeepSeek analiz bekleniyor...</p>
          <p className="text-[10px] mt-1 font-mono text-white/20">{data.error}</p>
        </div>
      ) : (
        <>
          {/* Seasonal Edge Banner */}
          {edge && (
            <div className="px-4 py-3 flex items-center justify-between border-b border-white/5" style={{ background: `${edgeColor}06` }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center border border-white/5" style={{ background: `${edgeColor}15`, borderColor: `${edgeColor}30` }}>
                  {edge.direction === "bullish" ? <TrendingUp className="w-5 h-5" style={{ color: edgeColor }} /> :
                    edge.direction === "bearish" ? <TrendingDown className="w-5 h-5" style={{ color: edgeColor }} /> :
                      <Activity className="w-5 h-5" style={{ color: edgeColor }} />}
                </div>
                <div>
                  <div className="text-sm font-bold font-mono" style={{ color: edgeColor, textShadow: `0 0 10px ${edgeColor}40` }}>
                    Seasonal {edge.direction?.toUpperCase()} Edge
                  </div>
                  <div className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>
                    Güven: {edge.confidence}%
                  </div>
                </div>
              </div>
            </div>
          )}
          {edge?.summary && (
            <div className="px-4 py-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
              <p className="text-[11px] font-mono leading-relaxed" style={{ color: "rgba(255,255,255,0.5)" }}>{edge.summary}</p>
            </div>
          )}

          {/* Monthly + Day of Week */}
          <div className="px-4 py-3 grid grid-cols-2 gap-2.5 border-b border-white/5">
            {/* Monthly Stats */}
            {data?.monthly_stats && (
              <div className="rounded-xl p-3 bg-white/5 border border-white/5">
                <div className="text-[9px] uppercase tracking-widest font-mono mb-2 text-white/30">
                  <Calendar className="w-3 h-3 inline mr-1" /> {data.monthly_stats.month}
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Win Rate</span>
                    <span className="text-sm font-bold font-mono" style={{ color: data.monthly_stats.historical_win_rate > 55 ? "#00ff88" : data.monthly_stats.historical_win_rate < 45 ? "#ff3366" : "#f0b429" }}>
                      %{data.monthly_stats.historical_win_rate}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Avg Return</span>
                    <span className="text-xs font-bold font-mono" style={{ color: data.monthly_stats.avg_return_pct > 0 ? "#00ff88" : "#ff3366" }}>
                      {data.monthly_stats.avg_return_pct > 0 ? "+" : ""}{data.monthly_stats.avg_return_pct?.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Performance</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{
                      background: data.monthly_stats.current_performance === "above_avg" ? "rgba(0,255,136,0.1)" : data.monthly_stats.current_performance === "below_avg" ? "rgba(255,51,102,0.1)" : "rgba(240,180,41,0.1)",
                      color: data.monthly_stats.current_performance === "above_avg" ? "#00ff88" : data.monthly_stats.current_performance === "below_avg" ? "#ff3366" : "#f0b429",
                    }}>{data.monthly_stats.current_performance?.replace("_", " ")}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Day of Week */}
            {data?.day_of_week && (
              <div className="rounded-xl p-3 bg-white/5 border border-white/5">
                <div className="text-[9px] uppercase tracking-widest font-mono mb-2 text-white/30">
                  <Clock className="w-3 h-3 inline mr-1" /> {data.day_of_week.day}
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Bias</span>
                    <span className="text-sm font-bold font-mono" style={{ color: biasColor(data.day_of_week.historical_bias) }}>
                      {data.day_of_week.historical_bias?.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Win Rate</span>
                    <span className="text-xs font-bold font-mono" style={{ color: data.day_of_week.win_rate > 55 ? "#00ff88" : "#f0b429" }}>
                      %{data.day_of_week.win_rate}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Avg Range</span>
                    <span className="text-xs font-mono text-white/60">{data.day_of_week.avg_range_pct?.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Session Analysis */}
          {data?.session_analysis && (
            <div className="px-4 py-3 border-b border-white/5">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-2 text-white/30">Session Analysis</div>
              <div className="grid grid-cols-3 gap-2">
                {(["asian", "london", "new_york"] as const).map((session) => {
                  const s = data.session_analysis?.[session];
                  if (!s) return null;
                  const sLabel = session === "new_york" ? "New York" : session.charAt(0).toUpperCase() + session.slice(1);
                  return (
                    <div key={session} className="rounded-xl p-2.5 text-center bg-white/5 border border-white/5">
                      <div className="flex justify-center mb-1">{sessionIcon(session)}</div>
                      <div className="text-[9px] font-mono mb-1 text-white/30">{sLabel}</div>
                      <div className="text-[10px] font-bold font-mono" style={{ color: biasColor(s.bias) }}>{s.bias?.toUpperCase()}</div>
                      <div className="text-[9px] font-mono mt-0.5 text-white/25">±{s.avg_range?.toFixed(1)}%</div>
                    </div>
                  );
                })}
              </div>
              {data.session_analysis.gap_fill_rate_pct != null && (
                <div className="mt-2 text-center">
                  <span className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>
                    Gap Fill Rate: <span style={{ color: "#00ccff" }}>{data.session_analysis.gap_fill_rate_pct}%</span>
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Upcoming Events */}
          {data?.upcoming_events && data.upcoming_events.length > 0 && (
            <div className="px-4 py-3 border-b border-white/5">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-2 text-white/30">
                <Zap className="w-3 h-3 inline mr-1 text-danger" /> Yaklaşan Olaylar
              </div>
              <div className="space-y-1.5">
                {data.upcoming_events.map((ev, i) => (
                  <div key={i} className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: `${impactColor(ev.impact)}06`, border: `1px solid ${impactColor(ev.impact)}10` }}>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: impactColor(ev.impact), boxShadow: `0 0 6px ${impactColor(ev.impact)}` }} />
                      <span className="text-[10px] font-mono text-white/70">{ev.event}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] font-mono" style={{ color: biasColor(ev.direction_bias) }}>{ev.direction_bias}</span>
                      <span className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${impactColor(ev.impact)}15`, color: impactColor(ev.impact) }}>
                        {ev.impact?.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomalies */}
          {data?.anomalies && data.anomalies.length > 0 && (
            <div className="px-4 py-3 border-b border-white/5">
              <div className="text-[9px] uppercase tracking-widest font-mono mb-2 text-white/30">
                <AlertTriangle className="w-3 h-3 inline mr-1 text-amber-400" /> Anomaliler
              </div>
              <div className="space-y-1.5">
                {data.anomalies.map((a, i) => (
                  <div key={i} className="rounded-lg px-3 py-2" style={{ background: `${sigColor(a.significance)}06`, border: `1px solid ${sigColor(a.significance)}10` }}>
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[10px] font-bold font-mono" style={{ color: sigColor(a.significance) }}>{a.type}</span>
                      <span className="text-[8px] font-mono px-1.5 py-0.5 rounded" style={{ background: `${sigColor(a.significance)}15`, color: sigColor(a.significance) }}>
                        {a.significance}
                      </span>
                    </div>
                    <p className="text-[10px] font-mono text-white/40">{a.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Reasoning */}
          {data?._reasoning && (
            <div className="px-4 py-2">
              <button onClick={() => setShowReasoning(!showReasoning)} className="flex items-center gap-1.5 text-[10px] font-mono w-full text-white/30">
                {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                AI Reasoning
              </button>
              {showReasoning && (
                <div className="mt-2 rounded-lg p-3 text-[10px] font-mono leading-relaxed whitespace-pre-wrap bg-black/30 text-white/35 max-h-[200px] overflow-y-auto">
                  {data._reasoning}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="px-4 py-2 text-center bg-black/20 border-t border-white/5">
        <p className="text-[10px] font-mono text-white/20">
          {lastUpdate ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}` : "Yükleniyor..."} | DeepSeek-R1
        </p>
      </div>
    </div>
  );
}
